"""
Twitter API adapter with sentiment analysis
"""

from typing import Dict, List, Optional, Union, Tuple
from datetime import datetime, timedelta
import tweepy
import pandas as pd
import numpy as np
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import re
from collections import defaultdict
from loguru import logger

from .base import APIAdapter

class TwitterSentiment:
    """Twitter sentiment data"""
    
    def __init__(
        self,
        text: str,
        created_at: datetime,
        polarity: float,
        subjectivity: float,
        compound_score: float,
        likes: int,
        retweets: int
    ):
        """
        Initialize sentiment
        
        Args:
            text: Tweet text
            created_at: Creation time
            polarity: TextBlob polarity
            subjectivity: TextBlob subjectivity
            compound_score: VADER compound score
            likes: Like count
            retweets: Retweet count
        """
        self.text = text
        self.created_at = created_at
        self.polarity = polarity
        self.subjectivity = subjectivity
        self.compound_score = compound_score
        self.likes = likes
        self.retweets = retweets
        
    @property
    def weighted_score(self) -> float:
        """Calculate weighted sentiment score"""
        # Combine TextBlob and VADER scores
        base_score = (self.polarity + self.compound_score) / 2
        
        # Weight by engagement
        engagement = self.likes + self.retweets
        if engagement > 0:
            weight = np.log1p(engagement)
        else:
            weight = 1.0
            
        return base_score * weight
        
    @property
    def sentiment_label(self) -> str:
        """Get sentiment label"""
        score = self.weighted_score
        if score > 0.2:
            return 'positive'
        elif score < -0.2:
            return 'negative'
        return 'neutral'

class TwitterAdapter(APIAdapter):
    """Twitter API adapter"""
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        access_token: str,
        access_token_secret: str,
        **kwargs
    ):
        """
        Initialize adapter
        
        Args:
            api_key: API key
            api_secret: API secret
            access_token: Access token
            access_token_secret: Access token secret
            **kwargs: Additional arguments
        """
        super().__init__(
            api_key,
            api_secret,
            'https://api.twitter.com/2',
            **kwargs
        )
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        
        # Initialize clients
        auth = tweepy.OAuthHandler(api_key, api_secret)
        auth.set_access_token(access_token, access_token_secret)
        self.client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret
        )
        
        # Initialize sentiment analyzer
        self.vader = SentimentIntensityAnalyzer()
        
    async def authenticate(self) -> bool:
        """
        Authenticate with API
        
        Returns:
            True if authenticated
        """
        try:
            self.client.get_me()
            return True
        except Exception as e:
            logger.error(f"Twitter authentication failed: {str(e)}")
            return False
            
    async def sign_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None
    ) -> Dict:
        """
        Sign API request
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            data: Request data
            
        Returns:
            Headers with signature
        """
        # Twitter authentication handled by tweepy
        return {}
        
    def clean_tweet(self, text: str) -> str:
        """
        Clean tweet text
        
        Args:
            text: Raw tweet text
            
        Returns:
            Cleaned text
        """
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text)
        
        # Remove mentions
        text = re.sub(r'@\w+', '', text)
        
        # Remove hashtags
        text = re.sub(r'#\w+', '', text)
        
        # Remove emojis
        text = text.encode('ascii', 'ignore').decode('ascii')
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
        
    def analyze_sentiment(
        self,
        text: str,
        created_at: datetime,
        likes: int,
        retweets: int
    ) -> TwitterSentiment:
        """
        Analyze tweet sentiment
        
        Args:
            text: Tweet text
            created_at: Creation time
            likes: Like count
            retweets: Retweet count
            
        Returns:
            Sentiment analysis
        """
        # Clean text
        clean_text = self.clean_tweet(text)
        
        # Get TextBlob sentiment
        blob = TextBlob(clean_text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        
        # Get VADER sentiment
        vader_scores = self.vader.polarity_scores(clean_text)
        compound_score = vader_scores['compound']
        
        return TwitterSentiment(
            text=text,
            created_at=created_at,
            polarity=polarity,
            subjectivity=subjectivity,
            compound_score=compound_score,
            likes=likes,
            retweets=retweets
        )
        
    async def search_tweets(
        self,
        query: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        max_results: int = 100
    ) -> List[TwitterSentiment]:
        """
        Search tweets with sentiment analysis
        
        Args:
            query: Search query
            start_time: Start time
            end_time: End time
            max_results: Maximum results
            
        Returns:
            List of analyzed tweets
        """
        try:
            # Search tweets
            tweets = self.client.search_recent_tweets(
                query=query,
                start_time=start_time,
                end_time=end_time,
                max_results=max_results,
                tweet_fields=['created_at', 'public_metrics']
            )
            
            # Analyze sentiments
            sentiments = []
            for tweet in tweets.data or []:
                metrics = tweet.public_metrics
                sentiment = self.analyze_sentiment(
                    text=tweet.text,
                    created_at=tweet.created_at,
                    likes=metrics['like_count'],
                    retweets=metrics['retweet_count']
                )
                sentiments.append(sentiment)
                
            return sentiments
            
        except Exception as e:
            logger.error(f"Error searching tweets: {str(e)}")
            return []
            
    async def get_user_tweets(
        self,
        username: str,
        max_results: int = 100
    ) -> List[TwitterSentiment]:
        """
        Get user tweets with sentiment analysis
        
        Args:
            username: Twitter username
            max_results: Maximum results
            
        Returns:
            List of analyzed tweets
        """
        try:
            # Get user ID
            user = self.client.get_user(username=username)
            if not user.data:
                return []
                
            # Get tweets
            tweets = self.client.get_users_tweets(
                id=user.data.id,
                max_results=max_results,
                tweet_fields=['created_at', 'public_metrics']
            )
            
            # Analyze sentiments
            sentiments = []
            for tweet in tweets.data or []:
                metrics = tweet.public_metrics
                sentiment = self.analyze_sentiment(
                    text=tweet.text,
                    created_at=tweet.created_at,
                    likes=metrics['like_count'],
                    retweets=metrics['retweet_count']
                )
                sentiments.append(sentiment)
                
            return sentiments
            
        except Exception as e:
            logger.error(f"Error getting user tweets: {str(e)}")
            return []
            
    async def analyze_crypto_sentiment(
        self,
        symbol: str,
        lookback_hours: int = 24
    ) -> Dict[str, Union[float, int, List[TwitterSentiment]]]:
        """
        Analyze cryptocurrency sentiment
        
        Args:
            symbol: Cryptocurrency symbol
            lookback_hours: Hours to look back
            
        Returns:
            Sentiment analysis results
        """
        try:
            # Build search query
            query = f"#{symbol} OR ${symbol} -is:retweet lang:en"
            
            # Get time range
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=lookback_hours)
            
            # Get tweets
            tweets = await self.search_tweets(
                query=query,
                start_time=start_time,
                end_time=end_time,
                max_results=100
            )
            
            if not tweets:
                return {
                    'average_score': 0.0,
                    'sentiment_counts': {
                        'positive': 0,
                        'neutral': 0,
                        'negative': 0
                    },
                    'tweet_count': 0,
                    'tweets': []
                }
                
            # Calculate metrics
            scores = [t.weighted_score for t in tweets]
            sentiments = [t.sentiment_label for t in tweets]
            
            # Count sentiments
            sentiment_counts = defaultdict(int)
            for s in sentiments:
                sentiment_counts[s] += 1
                
            return {
                'average_score': np.mean(scores),
                'sentiment_counts': dict(sentiment_counts),
                'tweet_count': len(tweets),
                'tweets': tweets
            }
            
        except Exception as e:
            logger.error(f"Error analyzing crypto sentiment: {str(e)}")
            return {
                'average_score': 0.0,
                'sentiment_counts': {
                    'positive': 0,
                    'neutral': 0,
                    'negative': 0
                },
                'tweet_count': 0,
                'tweets': []
            }
            
    async def get_trending_topics(
        self,
        woeid: int = 1  # Global
    ) -> List[str]:
        """
        Get trending topics
        
        Args:
            woeid: Location ID
            
        Returns:
            List of trending topics
        """
        try:
            # Get trends
            trends = self.client.get_place_trends(woeid)
            
            # Extract topics
            topics = []
            for trend in trends[0]['trends']:
                name = trend['name']
                if name.startswith('#'):
                    topics.append(name[1:])
                else:
                    topics.append(name)
                    
            return topics
            
        except Exception as e:
            logger.error(f"Error getting trending topics: {str(e)}")
            return []
