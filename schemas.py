"""
Database Schemas for Freelance Designer Booking Platform

Each Pydantic model represents a MongoDB collection. The collection name is the
lowercased class name (e.g., Freelancer -> "freelancer").
"""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime

# Core Users
class Freelancer(BaseModel):
    name: str = Field(..., description="Freelancer full name")
    email: str = Field(..., description="Contact email")
    skills: List[str] = Field(default_factory=list, description="Skill tags like frontend, backend, ux, devops")
    bio: Optional[str] = Field(None, description="Short bio")
    avatar_url: Optional[HttpUrl] = Field(None, description="Profile image URL")
    hourly_rate: Optional[float] = Field(None, ge=0, description="Rate per hour in USD")
    portfolio_links: List[HttpUrl] = Field(default_factory=list, description="External portfolio links")
    availability: List[dict] = Field(
        default_factory=list,
        description="List of available slots: {day: 'Mon', start: '09:00', end: '17:00', timezone: 'UTC'}"
    )

class PortfolioItem(BaseModel):
    freelancer_id: str = Field(..., description="Related freelancer id")
    title: str
    description: Optional[str] = None
    project_url: Optional[HttpUrl] = None
    image_url: Optional[HttpUrl] = None
    tags: List[str] = Field(default_factory=list)

class Reservation(BaseModel):
    business_name: str
    business_email: str
    freelancer_id: str
    start_time: datetime
    end_time: datetime
    notes: Optional[str] = None
    status: Literal['pending','confirmed','cancelled'] = 'pending'

class Advertisement(BaseModel):
    ad_type: Literal['business','freelancer']
    heading: str
    content: str
    # If business ad, include the designers responsible (names)
    designers: List[str] = Field(default_factory=list, description="Names of designers responsible for the advertised page")
    # Optional references
    business_name: Optional[str] = None
    freelancer_id: Optional[str] = None

class ForumThread(BaseModel):
    title: str
    content: str
    author_type: Literal['business','freelancer','guest'] = 'guest'
    author_name: str
    tags: List[str] = Field(default_factory=list)

class ForumPost(BaseModel):
    thread_id: str
    content: str
    author_name: str
