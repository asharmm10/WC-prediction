---
Task ID: 1
Agent: Main Agent
Task: Fix all UI/UX issues for FIFA World Cup 2026 Prediction League Django app

Work Log:
- Removed player parallax elements from base.html (caused mobile flickering, not visible)
- Removed floating footballs and particle canvas JS (caused mobile flickering)
- Simplified main.js to remove parallax, floating footballs, and particle canvas init
- Fixed CSS: removed player parallax, floating footballs, particles canvas styles
- Fixed match card CSS: changed from grid to flexbox layout for single-line team names
- Added .home-team and .away-team classes for crest positioning (home=name→crest, away=crest→name)
- Fixed mobile responsive: smaller logos, nowrap team names, text-overflow ellipsis
- Fixed nav active style: uses request.resolver_match.url_name for active class detection
- Added prominent next match card on home page with team logos and countdown
- Rewrote bracket.html with proper tree structure using bracket-tree CSS
- Removed admin participants from leaderboard (is_admin=False filter)
- Updated match_detail.html with fixed crest positions and scrollable predictions list
- Updated today.html with flexbox layout, crest positions, and click-through to match_detail
- Updated matches.html and schedule.html with new crest positioning
- Updated leaderboard.html to exclude admin
- Updated views.py, context_processors.py, templatetags to filter is_admin=False
- Copied missing team logos from upload assets to static folder

Stage Summary:
- All 8 user-requested changes have been implemented
- Player parallax removed (was causing flickering, not visible)
- Team names now display on single lines with crests positioned correctly
- Home team: name → crest (right of name), Away team: crest → name (left of name)
- Navigation active state now works using Django's resolver_match
- Next match displayed as prominent card on home page
- Bracket page uses tree structure with connecting lines between rounds
- Admin participants excluded from leaderboard
- Match cards redirect to match_detail for predictions
- Predictions visible to all users on match_detail page
- Django dev server runs on port 8000, accessible via gateway with ?XTransformPort=8000
