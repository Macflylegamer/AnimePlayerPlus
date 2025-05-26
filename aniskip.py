import requests
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import os
import re
import logging
import urllib.parse
import uuid  # Add at the top with other imports

logger = logging.getLogger(__name__)

class SkipType(Enum):
    OPENING = "op"
    ENDING = "ed"
    RECAP = "recap"
    MIXED_OP = "mixed-op"
    MIXED_ED = "mixed-ed"
    PREVIEW = "preview"

@dataclass
class SkipSegment:
    start: float
    end: float
    skip_type: SkipType
    episode_number: int
    anime_name: str

class AniSkip:
    API_BASE_URL = "https://api.aniskip.com/v2"
    SKIP_TIMES_URL = "https://api.aniskip.com/v2"
    MAL_API_URL = "https://api.jikan.moe/v4"
    
    def __init__(self, mpv_instance=None):
        self.skip_segments: List[SkipSegment] = []
        self.current_anime: Optional[str] = None
        self.current_episode: Optional[int] = None
        self.mpv = mpv_instance
        self.submitted_segments = set()  # Track which segments we've submitted
        self.submitter_id = str(uuid.uuid4())  # Generate a unique submitter ID
        
    def _extract_anime_info(self, filename: str) -> Tuple[Optional[str], Optional[int]]:
        """
        Extract anime name and episode number from filename.
        This is a basic implementation that can be improved based on your naming conventions.
        """
        # Remove file extension and path
        name = os.path.basename(filename).rsplit('.', 1)[0]
        
        # Common patterns for episode numbers
        patterns = [
            r'[Ee](\d+)',  # E01, e01
            r'[Ee]p(?:isode)?[.\s-]*(\d+)',  # Episode 01, Ep.01
            r'[Ss](\d+)[Ee](\d+)',  # S01E01
            r'[Ss]eason[.\s-]*(\d+)[.\s-]*[Ee]p(?:isode)?[.\s-]*(\d+)',  # Season 1 Episode 01
            r'[.\s-](\d{2,3})[.\s-]'  # -01-, .01.
        ]
        
        episode = None
        for pattern in patterns:
            match = re.search(pattern, name)
            if match:
                if len(match.groups()) > 1:  # For patterns with season and episode
                    episode = int(match.group(2))
                else:
                    episode = int(match.group(1))
                break
                
        if not episode:
            return None, None
            
        # Clean up anime name
        # Remove episode info
        anime_name = re.sub(r'[Ee]p(?:isode)?[.\s-]*\d+.*$', '', name)
        anime_name = re.sub(r'[Ee]\d+.*$', '', anime_name)
        anime_name = re.sub(r'[Ss]\d+[Ee]\d+.*$', '', anime_name)
        anime_name = re.sub(r'[Ss]eason[.\s-]*\d+[.\s-]*[Ee]p(?:isode)?[.\s-]*\d+.*$', '', anime_name)
        anime_name = re.sub(r'[.\s-]\d{2,3}[.\s-].*$', '', anime_name)
        
        # Remove common tags and quality indicators
        anime_name = re.sub(r'[.\s-]*(?:1080p|720p|480p|2160p|4K|HDR|WEB|BD|BDRip|BluRay|HDTV|WEBRip|WEB-DL|AMZN|NF|CR|SUB|DUB|MULTi|VOSTFR|VOST|VF|FRENCH|JAPANESE|ENGLISH)[.\s-]*', '', anime_name, flags=re.IGNORECASE)
        
        # Remove release group names (usually in brackets or parentheses)
        anime_name = re.sub(r'[\[\(].*?[\]\)]', '', anime_name)
        
        # Clean up extra spaces and dots
        anime_name = re.sub(r'[.\s-]+', ' ', anime_name).strip()
        
        if not anime_name:
            return None, None
            
        logger.debug(f"Extracted anime info - Name: {anime_name}, Episode: {episode}")
        return anime_name, episode

    def _get_mal_id(self, anime_name: str) -> Optional[int]:
        """Get MyAnimeList ID for an anime using Jikan API."""
        try:
            # URL encode the anime name
            encoded_name = urllib.parse.quote(anime_name)
            search_url = f"{self.MAL_API_URL}/anime?q={encoded_name}&sfw"
            logger.debug(f"Searching MAL API for: {anime_name}")
            
            response = requests.get(search_url)
            response.raise_for_status()
            data = response.json()
            
            if not data.get("data"):
                logger.debug(f"No MAL results found for: {anime_name}")
                return None
                
            # Find the best match
            best_match = None
            best_score = 0
            anime_name_lower = anime_name.lower()
            
            for result in data["data"]:
                result_name = result["title"].lower()
                # Calculate similarity score
                if anime_name_lower in result_name or result_name in anime_name_lower:
                    score = len(set(anime_name_lower.split()) & set(result_name.split()))
                    if score > best_score:
                        best_score = score
                        best_match = result
            
            if not best_match:
                logger.debug(f"No good MAL match found for: {anime_name}")
                return None
                
            mal_id = best_match["mal_id"]
            logger.debug(f"Found MAL ID {mal_id} for '{anime_name}' (matched with '{best_match['title']}')")
            return mal_id
            
        except requests.RequestException as e:
            logger.error(f"Error searching MAL API: {e}")
            return None

    def submit_skip_segment(self, mal_id: int, episode: int, skip_type: SkipType, start_time: float, end_time: float) -> bool:
        """Submit a new skip segment to AniSkip."""
        try:
            submit_url = f"{self.SKIP_TIMES_URL}/skip-times/{mal_id}/{episode}"
            
            # Get episode length from mpv
            episode_length = 0
            if self.mpv and hasattr(self.mpv, 'duration'):
                episode_length = float(self.mpv.duration)
            
            data = {
                "skipType": skip_type.value,
                "providerName": "AnimePlayer",
                "startTime": start_time,
                "endTime": end_time,
                "episodeLength": episode_length,
                "submitterId": self.submitter_id,  # Use the generated UUID
                "votes": 0,  # Required field
                "animeId": mal_id,  # Required field
                "episodeNumber": episode,  # Required field
                "submitDate": None,  # Will be set by server
                "skipId": None  # Will be set by server
            }
            
            logger.debug(f"Submitting skip segment: {data}")
            response = requests.post(submit_url, json=data)
            
            # Log the full response for debugging
            if response.status_code != 200:
                logger.error(f"Submit failed with status {response.status_code}: {response.text}")
                return False
                
            response.raise_for_status()
            result = response.json()
            
            if result.get("statusCode") == 200:
                logger.info(f"Successfully submitted skip segment for {skip_type.value}")
                return True
            else:
                logger.error(f"Failed to submit skip segment: {result.get('message')}")
                return False
                
        except requests.RequestException as e:
            logger.error(f"Error submitting skip segment: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response content: {e.response.text}")
            return False

    def fetch_skip_segments(self, filename: str) -> List[SkipSegment]:
        """Fetch skip segments for the current anime episode."""
        anime_name, episode = self._extract_anime_info(filename)
        if not anime_name or not episode:
            logger.debug(f"Could not extract anime info from filename: {filename}")
            return []
            
        self.current_anime = anime_name
        self.current_episode = episode
        
        try:
            # Get MAL ID first
            mal_id = self._get_mal_id(anime_name)
            if not mal_id:
                logger.debug(f"Could not find MAL ID for anime: {anime_name}")
                return []
            
            # Get skip segments using v2 API with MAL ID
            skip_url = f"{self.SKIP_TIMES_URL}/skip-times/{mal_id}/{episode}"
            params = {
                "types": ["op", "ed", "mixed-op", "mixed-ed", "recap"],
                "episodeLength": 0
            }
            logger.debug(f"Fetching skip segments from: {skip_url} with params: {params}")
            
            skip_response = requests.get(skip_url, params=params)
            
            # If no segments found (404), try to submit default segments
            if skip_response.status_code == 404:
                logger.info(f"No skip segments found for episode {episode}, attempting to submit default segments")
                
                # Only submit if we haven't already for this episode
                episode_key = f"{mal_id}_{episode}"
                if episode_key not in self.submitted_segments:
                    # Try to submit default OP (0-90s) and ED (last 90s) segments
                    if self.mpv and hasattr(self.mpv, 'duration'):
                        duration = float(self.mpv.duration)
                        # Submit OP - use more precise timing
                        if self.submit_skip_segment(mal_id, episode, SkipType.OPENING, 0.451, 90.451):  # Using same timing as episode 7
                            self.submitted_segments.add(episode_key)
                        # Submit ED - use more precise timing
                        if self.submit_skip_segment(mal_id, episode, SkipType.ENDING, duration - 90, duration):
                            self.submitted_segments.add(episode_key)
                        
                        # After submitting, try to fetch again
                        try:
                            retry_response = requests.get(skip_url, params=params)
                            if retry_response.status_code == 200:
                                skip_data = retry_response.json()
                                segments = []
                                for result in skip_data.get("results", []):
                                    try:
                                        skip_type = SkipType(result["skipType"])
                                        segment = SkipSegment(
                                            start=result["interval"]["startTime"],
                                            end=result["interval"]["endTime"],
                                            skip_type=skip_type,
                                            episode_number=episode,
                                            anime_name=anime_name
                                        )
                                        segments.append(segment)
                                        logger.debug(f"Added skip segment: {segment}")
                                    except (ValueError, KeyError) as e:
                                        logger.warning(f"Error processing skip segment: {e}")
                                        continue
                                self.skip_segments = segments
                                return segments
                        except requests.RequestException as e:
                            logger.error(f"Error fetching segments after submission: {e}")
                
                return []
                
            skip_response.raise_for_status()
            skip_data = skip_response.json()
            
            segments = []
            for result in skip_data.get("results", []):
                try:
                    skip_type = SkipType(result["skipType"])
                    segment = SkipSegment(
                        start=result["interval"]["startTime"],
                        end=result["interval"]["endTime"],
                        skip_type=skip_type,
                        episode_number=episode,
                        anime_name=anime_name
                    )
                    segments.append(segment)
                    logger.debug(f"Added skip segment: {segment}")
                except (ValueError, KeyError) as e:
                    logger.warning(f"Error processing skip segment: {e}")
                    continue
                    
            self.skip_segments = segments
            logger.debug(f"Found {len(segments)} skip segments")
            return segments
            
        except requests.RequestException as e:
            logger.error(f"Error fetching skip segments: {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"API Error details: {e.response.text}")
            return []
            
    def get_current_segment(self, current_time: float) -> Optional[SkipSegment]:
        """Get the current skip segment based on playback time."""
        for segment in self.skip_segments:
            if segment.start <= current_time <= segment.end:
                return segment
        return None
        
    def get_next_segment(self, current_time: float) -> Optional[SkipSegment]:
        """Get the next skip segment based on playback time."""
        for segment in sorted(self.skip_segments, key=lambda x: x.start):
            if segment.start > current_time:
                return segment
        return None 