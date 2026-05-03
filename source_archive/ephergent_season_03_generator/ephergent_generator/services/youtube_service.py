#!/usr/bin/env python3
"""YouTube Upload Service for the Google YouTube Data API.

This module provides a comprehensive service for authenticating with YouTube and 
uploading videos and thumbnails using OAuth 2.0. It handles credential management, 
video uploads with customizable metadata, and thumbnail setting.

Key Features:
- OAuth 2.0 authentication with token management
- Video upload with configurable metadata
- Custom thumbnail upload
- Error handling and logging

Requires:
- google-api-python-client
- google-auth-httplib2
- google-auth-oauthlib

Raises:
    ImportError: If required Google API libraries are not installed
"""

import os
import logging
from pathlib import Path
import mimetypes
from typing import Optional, List

# Third-party libraries for Google API
try:
    import google_auth_httplib2
    import google.oauth2.credentials
    import googleapiclient.discovery
    import googleapiclient.errors
    import googleapiclient.http
    from google_auth_oauthlib.flow import InstalledAppFlow
    import google.auth.transport.requests
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False
    # Define dummy classes/functions if google libs are not installed
    class DummyService:
        def videos(self): return self
        def thumbnails(self): return self
        def insert(self, *args, **kwargs): return self
        def set(self, *args, **kwargs): return self
        def execute(self, *args, **kwargs): return {'id': 'dummy_video_id'} if 'media_body' in kwargs else {}

    googleapiclient = None
    InstalledAppFlow = None
    google = None

# --- Constants ---
logger = logging.getLogger(__name__)

YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

# Configuration from Environment Variables or Defaults
SECRETS_DIR = Path(os.getenv('YOUTUBE_SECRETS_DIR', Path(__file__).parent.parent.parent / 'secrets'))
CLIENT_SECRETS_FILE = SECRETS_DIR / os.getenv('YOUTUBE_CLIENT_SECRET_FILE', 'client_secret.json')
TOKEN_FILE = SECRETS_DIR / os.getenv('YOUTUBE_TOKEN_FILE', 'token.json')
DEFAULT_CATEGORY_ID = os.getenv('YOUTUBE_CATEGORY_ID', '24')  # Default to '24' entertainment
DEFAULT_PRIVACY_STATUS = os.getenv('YOUTUBE_PRIVACY_STATUS', 'private')  # Default to 'private'


class YouTubeService:
    """A robust YouTube upload service using OAuth 2.0 authentication.

    Manages the complete workflow of YouTube video uploads, including:
    - OAuth 2.0 authentication and credential management
    - Video metadata configuration
    - Resumable video uploads
    - Custom thumbnail uploads

    Attributes:
        service (Optional[googleapiclient.discovery.Resource]): 
            Authenticated YouTube API service object.
        _authenticated (bool): Flag indicating authentication status.

    Requirements:
        - Requires client_secret.json for OAuth setup
        - Generates and manages token.json for credential persistence
        - Requires internet connection for authentication

    Note:
        - Supports single-user authentication flow
        - Automatically handles token refresh and re-authentication
        - Provides comprehensive logging for debugging
    """
    
    def __init__(self):
        self.service = None
        self._authenticated = False
    
    def get_authenticated_service(self) -> Optional[googleapiclient.discovery.Resource]:
        """Authenticate and obtain a YouTube Data API service object.

        Attempts to authenticate using stored credentials or initiates a new OAuth 2.0 flow.
        Handles token loading, refreshing, and saving for subsequent uses.

        Returns:
            Optional[googleapiclient.discovery.Resource]: Authenticated YouTube service object,
            or None if authentication fails.

        Raises:
            google.auth.exceptions.RefreshError: If token refresh fails
            google.auth.exceptions.AuthError: If authentication encounters an error

        Notes:
            - Uses local server flow which requires a browser environment
            - Saves and loads credentials from a local token file
            - Logs all authentication steps and potential failures
        """
        if not GOOGLE_API_AVAILABLE:
            logger.error("Google API client libraries not installed. Cannot authenticate.")
            return None

        creds = None
        if TOKEN_FILE.exists():
            try:
                creds = google.oauth2.credentials.Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
                logger.info(f"Loaded credentials from {TOKEN_FILE}")
            except Exception as e:
                logger.warning(f"Failed to load token file {TOKEN_FILE}: {e}. Will attempt re-authentication.")
                creds = None  # Force re-authentication

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Credentials expired. Refreshing token...")
                try:
                    creds.refresh(google.auth.transport.requests.Request())
                    logger.info("Token refreshed successfully.")
                except Exception as e:
                    logger.error(f"Failed to refresh token: {e}. Need new authentication.", exc_info=True)
                    creds = None  # Force re-authentication
            else:
                logger.info("No valid credentials found. Starting OAuth flow...")
                if not CLIENT_SECRETS_FILE.exists():
                    logger.error(f"Client secrets file not found at {CLIENT_SECRETS_FILE}. Cannot authenticate.")
                    return None
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS_FILE), SCOPES)
                    # Note: run_local_server requires a browser environment.
                    # For server environments, consider device flow or service accounts.
                    creds = flow.run_local_server(port=0)
                    logger.info("Authentication successful.")
                except Exception as e:
                    logger.error(f"Failed to run OAuth flow: {e}", exc_info=True)
                    return None

            # Save the credentials for the next run
            if creds:
                try:
                    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)  # Ensure directory exists
                    with open(TOKEN_FILE, 'w') as token:
                        token.write(creds.to_json())
                    logger.info(f"Credentials saved to {TOKEN_FILE}")
                except IOError as e:
                    logger.error(f"Failed to save token file to {TOKEN_FILE}: {e}")

        if not creds:
            logger.error("Could not obtain valid credentials.")
            return None

        # Build the service object
        try:
            self.service = googleapiclient.discovery.build(
                YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, credentials=creds
            )
            self._authenticated = True
            logger.info("YouTube API service built successfully.")
            return self.service
        except Exception as e:
            logger.error(f"Failed to build YouTube API service: {e}", exc_info=True)
            return None

    def upload_to_youtube(
        self,
        video_file_path: Path,
        title: str,
        description: str,
        tags: List[str],
        thumbnail_path: Optional[Path] = None,
        category_id: str = DEFAULT_CATEGORY_ID,
        privacy_status: str = DEFAULT_PRIVACY_STATUS,
    ) -> Optional[str]:
        """Upload a video and optionally a custom thumbnail to YouTube.

        This method handles the complete workflow of uploading a video to YouTube,
        including video metadata configuration, upload progress tracking, 
        and optional custom thumbnail setting.

        Args:
            video_file_path (Path): Absolute path to the video file to upload.
                Must be a valid video file accessible by the application.
            title (str): The title of the YouTube video (max 100 characters).
                Used to identify the video in YouTube search and recommendations.
            description (str): Detailed description of the video content.
                Supports Markdown and basic HTML formatting.
            tags (List[str]): A list of keywords associated with the video.
                Used to improve discoverability. Maximum of 30 tags recommended.
            thumbnail_path (Optional[Path], optional): Path to a custom thumbnail image.
                Must be a valid image file (PNG, JPG, GIF). Defaults to None.
            category_id (str, optional): YouTube video category ID.
                Defaults to '24' (Entertainment). See YouTube API documentation 
                for complete list of category IDs.
            privacy_status (str, optional): Video privacy setting.
                One of: 'private', 'unlisted', or 'public'. 
                Defaults to 'private' for content control.

        Returns:
            Optional[str]: The YouTube video ID if upload is successful, 
                           None if upload fails at any stage.

        Raises:
            ValueError: If video file or thumbnail is invalid.
            googleapiclient.errors.HttpError: For YouTube API-specific upload errors.

        Notes:
            - Uses resumable upload for large video files
            - Supports automatic MIME type detection
            - Provides progress logging during upload
            - Fails gracefully with detailed error logging

        Example:
            >>> service = YouTubeService()
            >>> video_path = Path('/path/to/video.mp4')
            >>> thumb_path = Path('/path/to/thumbnail.png')
            >>> video_id = service.upload_to_youtube(
            ...     video_path, 
            ...     title='My Awesome Video', 
            ...     description='A detailed video description', 
            ...     tags=['tutorial', 'tech'],
            ...     thumbnail_path=thumb_path
            ... )
            >>> if video_id:
            ...     print(f'Video uploaded successfully! URL: {service.get_video_url(video_id)}')
        """
        if not GOOGLE_API_AVAILABLE:
            logger.error("Google API client libraries not installed. Cannot upload video.")
            return None

        if not video_file_path.exists():
            logger.error(f"Video file not found: {video_file_path}")
            return None
        if thumbnail_path and not thumbnail_path.exists():
            logger.warning(f"Thumbnail file not found: {thumbnail_path}. Uploading without custom thumbnail.")
            thumbnail_path = None

        youtube = self.get_authenticated_service()
        if not youtube:
            logger.error("Failed to get authenticated YouTube service. Cannot upload.")
            return None

        logger.info(f"Starting YouTube upload for: {video_file_path.name}")
        logger.info(f"Title: {title}")
        logger.info(f"Category ID: {category_id}, Privacy: {privacy_status}")
        logger.debug(f"Description: {description[:100]}...")  # Log truncated description
        logger.debug(f"Tags: {tags}")

        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags,
                'categoryId': category_id
            },
            'status': {
                'privacyStatus': privacy_status
            }
        }

        # --- Upload Video ---
        video_id = None
        try:
            logger.info("Uploading video file...")
            # Determine video MIME type
            video_mime_type, _ = mimetypes.guess_type(str(video_file_path))
            if not video_mime_type or not video_mime_type.startswith('video/'):
                video_mime_type = 'application/octet-stream'  # Fallback
                logger.warning(f"Could not determine video MIME type for {video_file_path.name}. Using fallback '{video_mime_type}'.")

            media_video = googleapiclient.http.MediaFileUpload(
                str(video_file_path),
                mimetype=video_mime_type,
                resumable=True  # Use resumable uploads for large files
            )
            insert_request = youtube.videos().insert(
                part='snippet,status',
                body=body,
                media_body=media_video
            )

            # Execute the request with progress reporting
            response = None
            while response is None:
                status, response = insert_request.next_chunk()
                if status:
                    logger.info(f"Uploaded {int(status.progress() * 100)}%")
            video_id = response.get('id')
            if video_id:
                logger.info(f"Video uploaded successfully! Video ID: {video_id}")
            else:
                logger.error(f"Video upload failed. No ID received. Response: {response}")
                return None

        except googleapiclient.errors.HttpError as e:
            logger.error(f"An HTTP error {e.resp.status} occurred during video upload: {e.content}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred during video upload: {e}", exc_info=True)
            return None

        # --- Upload Thumbnail (if provided and video upload succeeded) ---
        if video_id and thumbnail_path:
            logger.info(f"Setting custom thumbnail from: {thumbnail_path.name}")
            try:
                # Determine thumbnail MIME type
                thumb_mime_type, _ = mimetypes.guess_type(str(thumbnail_path))
                if not thumb_mime_type or not thumb_mime_type.startswith('image/'):
                    logger.error(f"Could not determine or unsupported MIME type for thumbnail: {thumbnail_path}. Skipping thumbnail upload.")
                else:
                    media_thumbnail = googleapiclient.http.MediaFileUpload(
                        str(thumbnail_path),
                        mimetype=thumb_mime_type
                    )
                    thumbnail_request = youtube.thumbnails().set(
                        videoId=video_id,
                        media_body=media_thumbnail
                    )
                    thumbnail_response = thumbnail_request.execute()
                    logger.info(f"Custom thumbnail set successfully! Response: {thumbnail_response}")

            except googleapiclient.errors.HttpError as e:
                logger.error(f"An HTTP error {e.resp.status} occurred during thumbnail upload: {e.content}", exc_info=True)
                # Continue, returning the video_id, as the video itself was uploaded
            except Exception as e:
                logger.error(f"An unexpected error occurred during thumbnail upload: {e}", exc_info=True)
                # Continue, returning the video_id

        return video_id

    def is_authenticated(self) -> bool:
        """Check if the YouTube service is currently authenticated.

        Returns:
            bool: True if a valid service object exists and authentication is successful, 
                  False otherwise.

        Notes:
            - Provides a quick way to verify authentication status
            - Checks both service object and authentication flag
        """
        return self._authenticated and self.service is not None

    def get_video_url(self, video_id: str) -> str:
        """Generate a standard YouTube video watch URL.

        Args:
            video_id (str): The unique identifier for a YouTube video.

        Returns:
            str: A complete YouTube watch URL for the given video ID.

        Example:
            >>> yt_service = YouTubeService()
            >>> url = yt_service.get_video_url('dQw4w9WgXcQ')
            >>> print(url)
            'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
        """
        return f"https://www.youtube.com/watch?v={video_id}"