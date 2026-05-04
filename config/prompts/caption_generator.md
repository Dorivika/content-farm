Generate platform-specific captions for a short-form video.

**Title:** {{ title }}
**Hook:** {{ hook }}
**CTA:** {{ cta }}
**Tools mentioned:** {{ tools_needed }}

Generate three captions:

1. **YouTube Shorts:** Title (max 100 chars) + description with CTA and 3-5 hashtags.
2. **TikTok:** Punchier, conversational caption with 3-5 hashtags. Max 150 chars before hashtags.
3. **Instagram Reels:** First line is the hook. Then CTA. Then 3-5 hashtags. Max 2200 chars total.

Return ONLY a JSON object:
- youtube: { title: string, caption: string }
- tiktok: { caption: string }
- instagram: { caption: string }
