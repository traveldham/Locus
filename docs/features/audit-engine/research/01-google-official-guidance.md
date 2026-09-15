# Google's Official Guidance: What a Complete Business Profile Is, and What Affects Local Ranking

Research date: 2026-09-13. Every claim below is taken from Google's own Help Center or developer docs and cited inline. Where a page did not state a limit, that is noted rather than inferred.

## 1. Google's stated local ranking factors

Source: [Tips to improve your local ranking on Google](https://support.google.com/business/answer/7091)

Google says local results are "mainly based on relevance, distance, and prominence", and that "there's no way to request or pay for a better local ranking on Google."

- **Relevance** - "how well a Business Profile matches what someone is searching for." Google adds that "adding complete and detailed business information can help Google better understand your business and match your profile to relevant searches."
- **Distance** - "how far each business is from the customer who's searching" (or the location term used in the search).
- **Prominence** - "how well-known a business is." Google explicitly lists: links to the website, and "review count and review score" ("More reviews and positive ratings can help your business's local ranking"). Google also says position in web search results is a factor, so "SEO best practices apply."

The same page lists the actions Google recommends (these are Google's own "what to do" list, and so the backbone of any audit):

1. **Verify your business** - verified profiles are "more likely to show in local search results."
2. **Keep your business information up to date / complete** - full address, hours (incl. seasonal/special), business category, and attributes (e.g. parking, Wi-Fi). "Businesses with complete and accurate info are more likely to show up in local search results."
3. **Respond to reviews** - "When you reply to customer reviews, it shows that you value their feedback."
4. **Add photos & videos** - to show offerings and "tell the story of your business."
5. **Add in-store products** (eligible retailers) - products may appear in local results.

A related Help hub, [Make your Business Profile awesome](https://support.google.com/business/answer/6335804), groups the same items (verify, complete info, photos/videos, posts, chat, reviews, services, products, social links) and references a "Profile Strength" indicator.

## 2 & 3. Profile fields Google says to complete, with rules and API names

API names refer to the Business Information API `Location` resource: [accounts.locations reference](https://developers.google.com/my-business/reference/businessinformation/rest/v1/accounts.locations). Google states the API "shares the same list of required fields as the Business Profile UI" ([location-data](https://developers.google.com/my-business/content/location-data)); required at creation are title, primary category, phone, website and regular hours.

### 2.1 Business information

| Field | What "good" looks like / hard rules | API field |
|---|---|---|
| **Name** | Must be "your business's real-world name, as used consistently on your storefront, website, stationery." Prohibited: marketing taglines, store codes, trademark symbols, fully capitalised words, hours/status ("Open 24 hours"), phone numbers/URLs, special characters, service/product info ("4G LTE"), location details ("I-93 at Exit 2"), containment ("in Duane Reade"), repeated bilingual names. [Guidelines](https://support.google.com/business/answer/3038177) | `title` |
| **Categories** | One primary + up to **9 additional** ([Edit your Business Profile](https://support.google.com/business/answer/3039617)). Choose a category completing "This business IS a", not "HAS a"; "use as few categories as possible"; be "as specific as possible" (e.g. "Nail salon" not "Salon"); "Do not use categories solely as keywords or to describe attributes"; "Do not select a category for every product or service." You cannot create custom categories. Changing categories may trigger re-verification. [Manage your business category](https://support.google.com/business/answer/7249669), [Guidelines](https://support.google.com/business/answer/3038177) | `categories.primaryCategory`, `categories.additionalCategories` |
| **Address** | "Precise, accurate address"; no P.O. boxes or remote mailboxes; include suite/floor; nothing in address lines that isn't the physical location; one profile per location; must have permanent signage. Max 5 address lines in API. [Guidelines](https://support.google.com/business/answer/3038177) | `storefrontAddress` |
| **Service area** | Service-area businesses: one profile per central office; hide address if operating from home; area "shouldn't extend farther than about 2 hours of driving time." API allows max 20 places. [Guidelines](https://support.google.com/business/answer/3038177) | `serviceArea` |
| **Phone** | "Use a local phone number instead of a central call center helpline"; no premium numbers; no redirects to landing pages; fax numbers not allowed; primary + up to 2 additional. [Guidelines](https://support.google.com/business/answer/3038177), [Edit profile](https://support.google.com/business/answer/3039617) | `phoneNumbers.primaryPhone`, `phoneNumbers.additionalPhones` |
| **Website** | Must include `http://` or `https://`; must not redirect; API doc says "preferably location-specific." [Edit profile](https://support.google.com/business/answer/3039617) | `websiteUri` |
| **Description** | Max **750 characters**; no URLs or HTML; "focus primarily on details about your business instead of details about promotions, prices, or sales"; no links "of any type"; no "low-quality, irrelevant, or distracting content." API notes the profile description is required for all categories except lodging. [Edit profile](https://support.google.com/business/answer/3039617), [Guidelines](https://support.google.com/business/answer/3038177), [Manage description](https://support.google.com/business/answer/13682007) | `profile.description` |
| **Opening date** | Month and year only; may be up to one year in the future; future-dated profiles appear 90 days before opening. [Add an opening date](https://support.google.com/business/answer/9174409) | `openInfo.openingDate`, `openInfo.status` (OPEN / CLOSED_TEMPORARILY / CLOSED_PERMANENTLY) |
| **Regular hours** | Provide "regular customer-facing hours of operation." Some categories (hotels, schools, theaters, airports, venues) are excluded. Restaurants use dine-in hours; banks use lobby hours. [Guidelines](https://support.google.com/business/answer/3038177), [Edit hours](https://support.google.com/business/answer/15300403) | `regularHours` |
| **Special hours** | For holidays/events; only when hours change "for up to 6 days in a row" (longer = mark temporarily closed). Google recommends confirming hours for official holidays "even if they're the same as your regular hours." [Special hours](https://support.google.com/business/answer/6303076) | `specialHours` |
| **More hours** | Types include drive-through, delivery, takeout, pickup (and senior hours etc.); "More hours don't display until you first set regular hours"; should be a subset of primary hours. [More hours](https://support.google.com/business/answer/9876800) | `moreHours[].hoursTypeId` |
| **Social links** | One link per platform (Facebook, Instagram, LinkedIn, Pinterest, TikTok, X, YouTube). [Edit profile](https://support.google.com/business/answer/3039617) | (attribute) |
| **Labels / store code** | Free-form tags, 1-255 chars; internal only. | `labels`, `storeCode` |

### 2.2 Attributes

Source: [Manage your business attributes](https://support.google.com/business/answer/9049526), [Attributes (API)](https://developers.google.com/my-business/content/attributes)

- Two classes: **factual/objective** (accessibility such as wheelchair access, Wi-Fi, payment methods, recycling, amenities) which the owner sets, and **identity** attributes (Women-owned, Black-owned, LGBTQ+ owned, Veteran-owned, etc.) which are opt-in. Subjective attributes (e.g. "cozy") come from user opinions and are not editable.
- Availability "varies by category and country"; Google's ranking page names parking and Wi-Fi as examples of attributes to fill.
- API: `locations.attributes` / `locations.updateAttributes` with `attributeMask`; value types BOOL, ENUM, REPEATED_ENUM, URL. Fetch the supported set via `attributes.list?categoryName=gcid:...&regionCode=..&languageCode=..` - "Attributes are dynamic and should be retrieved often." URL attributes include `attributes/url_menu`, `url_order_ahead`, `url_appointment`.
- Review of edits "usually takes about 10 minutes, but sometimes it can take up to 30 days."

### 2.3 Photos and videos

Source: [Business Profile photo & video guidelines](https://support.google.com/business/answer/6103862), [Photos & videos policy](https://support.google.com/business/answer/7213077)

- Types: **logo**, **cover photo**, and business photos (exterior, interior, products, team, at work).
- Photos: JPG or PNG; 10 KB - 5 MB; recommended 720 x 720 px; minimum 250 x 250 px; "in focus and well lit, and have no significant alterations or excessive use of filters."
- Videos: up to 30 seconds; up to 75 MB; 720p or higher.
- Media shows only after verification; review can take 24-48 hours.
- Google's ranking page recommends adding photos and videos to "tell the story of your business"; no count target is stated.
- API: `accounts.locations.media` (v4).

### 2.4 Posts

Source: [Create & manage posts](https://support.google.com/business/answer/7342169), [Posts content policy](https://support.google.com/business/answer/7662907), [LocalPost API](https://developers.google.com/my-business/reference/rest/v4/accounts.locations.localPosts)

- Types: **Update** (description, photo/video, optional action button), **Offer** (requires title, dates, time; auto "View offer" button; optional coupon code, link, terms), **Event** (requires title, start/end dates and times; defaults to 24-hour event).
- "Posts older than 6 months are archived unless a date range is set." Posts can be scheduled or recur.
- Rules: professional and family-friendly; no offensive or sexually explicit content; no phone numbers in descriptions (may be rejected); avoid misspellings, extra characters, auto-generated or "text that adds no value"; regulated industries must not post about the regulated products.
- API: `topicType` STANDARD / EVENT / OFFER / ALERT; `callToAction.actionType` BOOK, ORDER, SHOP, LEARN_MORE, SIGN_UP, CALL; `state` LIVE/PROCESSING/SCHEDULED/REJECTED/RECURRING. Product posts cannot be created via API ([posts-data](https://developers.google.com/my-business/content/posts-data)). No character limit is stated in the current docs.

### 2.5 Reviews

Source: [Maps user contributed content policy](https://support.google.com/contributionpolicy/answer/7400114), [Reply to reviews](https://support.google.com/business/answer/3474122), [Ranking tips](https://support.google.com/business/answer/7091)

- Ranking: "More reviews and positive ratings can help your business's local ranking"; replying "shows that you value their feedback."
- Replying: be prompt; personalise; keep short; not promotional; for negative reviews acknowledge mistakes, apologise where warranted, never share private info, offer to take it offline; sign with name/initials.
- Merchants may "encourage the posting of content that does represent a genuine experience, without offering incentives," but must not pay/incentivise, "require or pressure users to leave ratings or write reviews while on the premises," solicit specific content, or gate reviews.
- API: `accounts.locations.reviews` (v4) with `reviewReply`.

### 2.6 Q&A - discontinued

Google discontinued the Q&A API on **3 November 2025**: "we will be discontinuing the My Business Q&A API as we are in the process of updating the Q&A functionality and user experience"; NEW_QUESTION/NEW_ANSWER notifications are deprecated ([Q&A API change log](https://developers.google.com/my-business/content/qanda/change-log)). The Edit-profile page still lists Q&A as available only for "select business categories and regions." Treat Q&A as not auditable via API.

### 2.7 Messaging / chat

Source: [Chat with customers](https://support.google.com/business/answer/15013580), [Changes to chat and call history](https://support.google.com/business/answer/14919056)

- Since 31 July 2024 the native GBP chat and call history are gone; businesses add a **WhatsApp click-to-chat URL or SMS number** to contact info instead. Requires a claimed and verified profile; available in select regions; if both are added "only the text message option will be shown."
- Historical guidance (still surfaced on support pages): reply within 24 hours or Google may remove the chat button.
- Performance API still exposes `BUSINESS_CONVERSATIONS`.

### 2.8 Products, services, menu

- **Products** ([Product editor](https://support.google.com/business/answer/9124203), [Showcase in-store products](https://support.google.com/business/answer/9934993)): for local stores selling physical goods; fields are name, category, price, description, photo, link; must comply with Shopping policies or all uploaded products can be removed; eligible countries US, CA, UK, IE (Pointy/Merchant Center automation also AU). Google's ranking page says products may appear in local results.
- **Services** ([Manage services](https://support.google.com/business/answer/9455399)): pick Google-suggested structured services per category or add custom ones; group by category; add description and price. Custom service names must not contain "profanity, gibberish, personal information, prices, or phone numbers." API: `serviceItems[]` (structured `serviceTypeId` or `freeFormServiceItem`).
- **Menu** ([Menu editor](https://support.google.com/business/answer/9455840)): food & drink businesses only; items with name, description, price, photo, grouped into sections; 24-48 h to publish; API-supplied menus are not editable in the UI. Attribute `url_menu` for a menu link.

### 2.9 Bookings

Source: [Set up bookings through a provider](https://support.google.com/business/answer/7475773)

Two options: a Reserve with Google partner (blue booking CTA, shows "within a week", performance data available; `BUSINESS_BOOKINGS` metric) or your own booking link (no performance data). Restaurant waitlist requires an RwG partner. Attribute `url_appointment` covers the self-supplied link.

### 2.10 Verification / Voice of Merchant

Source: [Verify your business](https://support.google.com/business/answer/7107242), [getVoiceOfMerchantState](https://developers.google.com/my-business/reference/verifications/rest/v1/locations/getVoiceOfMerchantState)

- Verification unlocks editing and customer interaction, is the first ranking tip, and is required before photos show. Methods: phone/SMS, email, video call, postcard (up to 14 days); codes expire after 30 days; don't edit info during verification.
- API `VoiceOfMerchantState`: `hasVoiceOfMerchant` ("in good standing and has control over the business on Google"), `hasBusinessAuthority`, plus next-step objects `verify`, `waitForVoiceOfMerchant`, `complyWithGuidelines` (suspended/disabled), `resolveOwnershipConflict` (duplicate).

### 2.11 Performance metrics Google exposes

[DailyMetric enum](https://developers.google.com/my-business/reference/performance/rest/v1/DailyMetric): BUSINESS_IMPRESSIONS_{DESKTOP,MOBILE}_{MAPS,SEARCH}, BUSINESS_CONVERSATIONS, BUSINESS_DIRECTION_REQUESTS, CALL_CLICKS, WEBSITE_CLICKS, BUSINESS_BOOKINGS, BUSINESS_FOOD_ORDERS, BUSINESS_FOOD_MENU_CLICKS. Impressions are deduplicated per user per day.

## 4. What Google says does NOT help, or is prohibited

- "There's no way to request or pay for a better local ranking on Google." ([7091](https://support.google.com/business/answer/7091))
- Keywords, taglines, hours, phone numbers, URLs, service or location descriptors in the business name. ([3038177](https://support.google.com/business/answer/3038177))
- Using categories "solely as keywords," or one category per product/service. ([3038177](https://support.google.com/business/answer/3038177), [7249669](https://support.google.com/business/answer/7249669))
- P.O. boxes, virtual offices, multiple profiles per location, service areas beyond ~2 hours' drive. ([3038177](https://support.google.com/business/answer/3038177))
- Call-centre, premium, or redirecting phone numbers and URLs. ([3038177](https://support.google.com/business/answer/3038177))
- Links, promotions or prices in the description. ([3038177](https://support.google.com/business/answer/3038177), [3039617](https://support.google.com/business/answer/3039617))
- Paid/incentivised reviews, review gating, pressuring customers on-premises, reviews from staff/family, bulk or patterned review activity. ([contributionpolicy](https://support.google.com/contributionpolicy/answer/7400114))
- Phone numbers in post descriptions; filler/auto-generated post text; regulated-product content in posts. ([7662907](https://support.google.com/business/answer/7662907))
- Heavily filtered or altered photos. ([6103862](https://support.google.com/business/answer/6103862))
- Prices or phone numbers inside custom service names. ([9455399](https://support.google.com/business/answer/9455399))

## Gaps in Google's documentation (for the engine)

Google does not publish: a photo count target, a post cadence, a post character limit (current pages), a review-count threshold, or a numeric "profile strength" formula. Any such thresholds in the audit engine are heuristics, not Google policy, and should be labelled as such.
