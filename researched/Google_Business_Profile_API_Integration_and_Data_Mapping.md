# Google Business Profile API Integration, Sync, Data Mapping & Write Capabilities

**Research date:** 12 September 2026  
**Purpose:** Developer-facing reference for connecting a user's Google Business Profile (GBP) to an application, synchronizing available data, understanding the JSON returned by Google, performing supported profile-management actions, and comparing Google-exposed data with the supplied Locus assignment dataset.

> Important: Google Business Profile API access is gated, OAuth-based, quota-limited, and policy-controlled. Some older `mybusiness.googleapis.com/v4` resources remain documented alongside newer split v1 services. Always verify the current method before implementation.

---

# 1. Executive Answer

## Can a user connect their Google Business Profile to our app?

**Yes.**

The supported flow is:

```text
User
  ↓
"Connect Google Business Profile"
  ↓
Google OAuth 2.0
  ↓
User signs into Google manually
  ↓
Google consent screen
  ↓
User explicitly grants permission
  ↓
Our backend receives authorization
  ↓
List GBP accounts
  ↓
List accessible locations
  ↓
User selects / confirms locations
  ↓
Initial synchronization
  ↓
Periodic + event-driven updates
```

The principal OAuth scope used by the Business Profile APIs is:

```text
https://www.googleapis.com/auth/business.manage
```

With appropriate authorization, supported APIs can read and/or manage:

- accounts and accessible locations;
- business name/title;
- store code;
- phone numbers;
- website;
- address;
- primary and additional categories;
- regular hours;
- special hours;
- service-area information;
- profile description;
- open/closed state;
- services/service items;
- attributes;
- certain Google-suggested updates;
- verification / Voice of Merchant state;
- performance metrics;
- monthly search keywords;
- reviews;
- owner review replies;
- merchant media;
- customer-contributed media metadata;
- local posts;
- place-action links;
- some category-specific data such as food menus;
- notifications for supported GBP events;
- eligible business-call aggregate insights.

It can also perform supported write actions such as:

- edit profile fields;
- update hours;
- update attributes;
- manage service items where supported;
- create/update/delete local posts;
- upload/delete/manage merchant media;
- reply to reviews and update/delete the owner's reply;
- manage place-action links such as appointment/order URLs;
- perform supported verification workflows when specifically requested by the owner.

However, the GBP APIs **do not provide everything in the supplied assignment dataset**.

In particular, these supplied datasets are **not standard GBP management/performance API outputs**:

```text
tracked_keywords.csv
keyword_rank_weekly.csv
competitor_ranks_weekly.csv
booking_requests.csv
```

Those require other sources.

---

# 2. Google Cloud / GBP API Access Prerequisites

Before users can connect profiles, the application itself needs Google Business Profile API access.

Google's current prerequisites include:

1. Google Account.
2. Google Cloud project.
3. Google Business Profile Organization account.
4. A verified, active GBP managed for 60+ days.
5. A website representing the business on that GBP.
6. Application for Basic GBP API access.
7. Approval from Google.
8. Enable required GBP APIs in the approved Cloud project.
9. Configure OAuth consent screen.
10. Create OAuth 2.0 client credentials.

Google states that a project with:

```text
0 QPM
```

has not been approved, while an approved project normally shows the standard quota such as:

```text
300 QPM
```

for relevant APIs.

Official prerequisite documentation:

https://developers.google.com/my-business/content/prereqs

---

# 3. OAuth Connection Architecture

## 3.1 User-facing flow

Recommended UX:

```text
Settings
   ↓
Integrations
   ↓
Google Business Profile
   ↓
[ Connect Google Business Profile ]
   ↓
Google sign-in
   ↓
Consent
   ↓
Return to our application
   ↓
Choose Account
   ↓
Choose Locations
   ↓
Sync
```

Google requires OAuth 2.0 authorization for Business Profile API requests.

Do not ask the user for:

- Google password;
- Business Profile password;
- browser cookies;
- copied session tokens.

Use OAuth.

---

## 3.2 Recommended OAuth mode

For a server-side SaaS application:

```text
Authorization Code flow
+
offline access / refresh token
```

Conceptual flow:

```text
Browser
  │
  ├── GET /integrations/google/connect
  │
  ▼
Google OAuth
  │
  ├── User logs in
  ├── User sees consent
  └── Google redirects back
          │
          ▼
GET /oauth/google/callback?code=...
          │
          ▼
Backend exchanges code
          │
          ▼
access_token
refresh_token
expires_in
scope
          │
          ▼
Store refresh token encrypted
```

The access token is short-lived.

The refresh token lets the backend obtain new access tokens without forcing the merchant to sign in every sync.

---

## 3.3 Scope

Main scope:

```text
https://www.googleapis.com/auth/business.manage
```

Request only scopes actually needed.

---

## 3.4 Suggested internal connection record

```json
{
  "connection_id": "gconn_123",
  "organization_id": "org_1001",
  "provider": "google_business_profile",
  "google_user_reference": "internal_reference",
  "scope": [
    "https://www.googleapis.com/auth/business.manage"
  ],
  "status": "active",
  "connected_at": "2026-09-12T13:40:00Z",
  "last_successful_sync_at": "2026-09-12T14:00:00Z"
}
```

Do **not** expose OAuth tokens to the browser after connection.

Store refresh tokens:

- encrypted at rest;
- in a secret-management system or protected credentials store;
- with strict service-level access;
- never in application logs.

---

# 4. Important Third-Party API Policy Constraint

This matters greatly for a SaaS product.

Google allows tools that help authorized business owners manage their profiles, but the current GBP API policy places restrictions on indirect/programmatic third-party access.

Key implications:

1. End users must manually sign in.
2. The merchant must explicitly authorize access.
3. Do not create a public proxy API that lets customers script GBP actions through your Google project to avoid Google's access requirements.
4. Automated actions such as review replies, listing edits, or similar changes cannot be triggered without the user's prior **specific and express consent**.
5. A disconnect/revocation workflow should be available.
6. Some workflows, such as ownership claims, require merchant involvement.
7. Verification must only be initiated on the direct request of the business owner.

This is not merely an OAuth issue; it affects the product architecture.

Recommended pattern:

```text
User opens our UI
   ↓
Our system recommends a change
   ↓
User explicitly clicks "Apply"
   ↓
Backend calls Google API
   ↓
Audit log stores action
```

Avoid:

```text
AI decides a change
   ↓
Automatically modifies GBP
without explicit merchant approval
```

Official policy:

https://developers.google.com/my-business/content/policies

---

# 5. Content Storage Warning

Google's current Business Profile API policy places significant restrictions on storing API "Content".

The policy states that Business Profile API Content generally cannot be prefetched, cached, indexed, or stored outside the project except limited amounts for performance, and permitted stored Content must be temporary, secure, no more than 30 calendar days, and not manipulated/aggregated in prohibited ways.

This affects architecture for:

- data warehouses;
- long-term raw API history;
- model training;
- review archives;
- raw Google media metadata;
- long-lived analytics snapshots.

Therefore **do not assume that every raw Google API response can simply be retained forever for ML**.

Before production, classify every field as one of:

```text
Google API Content
Merchant-provided/merchant-owned first-party data
Our own operational data
Our derived model output
Our recommendation/action logs
CRM/POS/booking data
Third-party rank data
```

Then design retention around the applicable terms.

This should receive legal/policy review before building a permanent ML lake.

---

# 6. Main Google Business Profile APIs

Google has split GBP functionality across multiple API services.

| API | Main use |
|---|---|
| Account Management API | Accounts, access/management relationships |
| Business Information API | Core location/profile data |
| Business Profile Performance API | Daily performance metrics + monthly search terms |
| Notifications API | Pub/Sub event notifications |
| Verifications API | Verification options, verification flow, Voice of Merchant |
| Place Actions API | Appointment/order/reservation/shop links |
| Business Calls API | Eligible call insight aggregates |
| Legacy Google My Business v4 resources | Reviews, posts, media and some older/category-specific operations |
| Category-specific resources | Food menus, lodging-related data, etc. where eligible |

---

# 7. Core Service Endpoints

Common service roots include:

```text
Business Information
https://mybusinessbusinessinformation.googleapis.com/v1/

Performance
https://businessprofileperformance.googleapis.com/v1/

Notifications
https://mybusinessnotifications.googleapis.com/v1/

Verifications
https://mybusinessverifications.googleapis.com/v1/

Place Actions
https://mybusinessplaceactions.googleapis.com/v1/

Business Calls
https://mybusinessbusinesscalls.googleapis.com/v1/

Legacy / remaining v4 resources
https://mybusiness.googleapis.com/v4/
```

Do not assume all functionality moved to one modern endpoint.

---

# 8. Initial Sync Sequence

After OAuth succeeds, perform synchronization in stages.

```text
OAuth successful
      ↓
Fetch accessible accounts
      ↓
Fetch accessible locations
      ↓
For each selected location
      │
      ├── Business Information
      ├── Attributes
      ├── Performance metrics
      ├── Search keywords
      ├── Reviews + owner replies
      ├── Merchant media
      ├── Customer media metadata
      ├── Local posts
      ├── Place-action links
      ├── Voice of Merchant / verification
      └── Eligible category-specific data
      ↓
Normalize
      ↓
Feature calculation
      ↓
Recommendation engine
```

For a large account, put location synchronization into a queue.

Do not block an HTTP request while fetching hundreds of locations.

---

# 9. Accounts

An Account is the container/access context for locations.

Conceptual response shape:

```json
{
  "name": "accounts/123456789",
  "accountName": "Example Dental Group",
  "type": "BUSINESS",
  "role": "PRIMARY_OWNER",
  "verificationState": "VERIFIED",
  "vettedState": "VETTED",
  "accountNumber": "1234567890",
  "permissionLevel": "OWNER_LEVEL"
}
```

Useful application data:

```text
Google account resource ID
Account display name
Account type
User role / access level
Verification state
```

Your own app should maintain:

```text
organization_id ↔ Google account resource
```

separately.

---

# 10. Business Information API — Location Data

Current Business Information Location shape includes fields such as:

```json
{
  "name": "locations/987654321",
  "languageCode": "en",
  "storeCode": "TX-AUS-01",
  "title": "Example Dental Austin",
  "phoneNumbers": {
    "primaryPhone": "+1 512 555 0100"
  },
  "categories": {
    "primaryCategory": {
      "name": "categories/gcid:dentist",
      "displayName": "Dentist"
    },
    "additionalCategories": []
  },
  "storefrontAddress": {
    "regionCode": "US",
    "postalCode": "78701",
    "administrativeArea": "TX",
    "locality": "Austin",
    "addressLines": [
      "100 Example Street"
    ]
  },
  "websiteUri": "https://example.com/austin",
  "regularHours": {
    "periods": []
  },
  "specialHours": {
    "specialHourPeriods": []
  },
  "labels": [
    "south-region"
  ],
  "openInfo": {
    "status": "OPEN",
    "openingDate": {
      "year": 2019,
      "month": 8,
      "day": 1
    }
  },
  "profile": {
    "description": "Example location description."
  },
  "serviceItems": []
}
```

Other available structures include:

- service area;
- relationships to parent/child locations;
- extra/more-hours types;
- location metadata;
- latitude/longitude in specific circumstances;
- Google update state;
- Maps URI;
- new-review URI;
- eligibility flags.

---

# 11. Important Location Metadata

Business Information metadata can expose information such as:

```text
hasGoogleUpdated
hasPendingEdits
canDelete
canOperateLocalPost
canModifyServiceList
canHaveFoodMenus
canOperateHealthData
canOperateLodgingData
placeId
duplicateLocation
mapsUri
newReviewUri
canHaveBusinessCalls
hasVoiceOfMerchant
```

This is useful for deciding which actions your UI should offer.

Example:

```text
if canHaveFoodMenus == false
    do not show "Manage Food Menu"
```

---

# 12. Hours

Google's hours structure is richer than the supplied `location_hours.csv`.

Google:

```json
{
  "regularHours": {
    "periods": [
      {
        "openDay": "MONDAY",
        "openTime": {
          "hours": 9,
          "minutes": 0
        },
        "closeDay": "MONDAY",
        "closeTime": {
          "hours": 17,
          "minutes": 0
        }
      }
    ]
  }
}
```

Google also exposes:

```text
specialHours
moreHours
```

Therefore your production schema should support:

```text
location_regular_hours
location_special_hours
location_more_hours
```

instead of only one opening and closing time per weekday.

---

# 13. Attributes

Attributes vary dynamically by:

```text
business category
country
```

Examples might include:

```text
accessibility
payments
amenities
services
identity-related fields
```

Do not hard-code one universal list.

Fetch supported attributes for the location category/country.

Example listing values:

```json
{
  "name": "locations/987654321/attributes",
  "attributes": [
    {
      "name": "attributes/has_wheelchair_accessible_seating",
      "valueType": "BOOL",
      "values": [
        false
      ]
    },
    {
      "name": "attributes/wi_fi",
      "valueType": "ENUM",
      "values": [
        "free_wi_fi"
      ]
    }
  ]
}
```

Supported actions:

```text
GET configured attributes
GET Google-updated/live attribute view
PATCH supported merchant attributes
```

The catalog can change over time.

Official docs:

https://developers.google.com/my-business/content/attributes

---

# 14. Services

Business Information can expose `serviceItems`.

Conceptually:

```json
{
  "serviceItems": [
    {
      "structuredServiceItem": {
        "serviceTypeId": "service-type-id"
      },
      "price": {
        "currencyCode": "USD",
        "units": "120"
      }
    }
  ]
}
```

A production product can potentially recommend:

```text
Missing services
Price missing
Services not aligned with available category service types
```

subject to category support and current API behavior.

---

# 15. Performance Metrics

The current Business Profile Performance API supports daily time-series metrics.

Endpoint pattern:

```text
GET
https://businessprofileperformance.googleapis.com/v1/
locations/{locationId}:fetchMultiDailyMetricsTimeSeries
```

Requested metrics can include:

```text
BUSINESS_IMPRESSIONS_DESKTOP_MAPS
BUSINESS_IMPRESSIONS_DESKTOP_SEARCH
BUSINESS_IMPRESSIONS_MOBILE_MAPS
BUSINESS_IMPRESSIONS_MOBILE_SEARCH
BUSINESS_CONVERSATIONS
BUSINESS_DIRECTION_REQUESTS
CALL_CLICKS
WEBSITE_CLICKS
BUSINESS_BOOKINGS
BUSINESS_FOOD_ORDERS
BUSINESS_FOOD_MENU_CLICKS
```

Conceptual request:

```text
dailyMetrics=CALL_CLICKS
dailyMetrics=WEBSITE_CLICKS
dailyMetrics=BUSINESS_DIRECTION_REQUESTS
dailyRange.startDate...
dailyRange.endDate...
```

Conceptual normalized Google response:

```json
{
  "multiDailyMetricTimeSeries": [
    {
      "dailyMetricTimeSeries": [
        {
          "dailyMetric": "CALL_CLICKS",
          "timeSeries": {
            "datedValues": [
              {
                "date": {
                  "year": 2026,
                  "month": 9,
                  "day": 1
                },
                "value": "18"
              }
            ]
          }
        }
      ]
    }
  ]
}
```

Your backend should pivot this into:

```text
location_id
date
metric
value
```

or a daily fact table.

---

# 16. Search Keywords

Google provides monthly search-query impression information for the merchant's **own listing**.

Endpoint:

```text
GET
/v1/locations/{locationId}/searchkeywords/impressions/monthly
```

Example response:

```json
{
  "searchKeywordsCounts": [
    {
      "searchKeyword": "dentist near me",
      "insightsValue": {
        "value": "168"
      }
    },
    {
      "searchKeyword": "emergency dentist",
      "insightsValue": {
        "threshold": "15"
      }
    }
  ],
  "nextPageToken": "..."
}
```

Important:

`insightsValue` can contain either:

```text
value
```

or:

```text
threshold
```

The API describes this as search keywords used to find the business in Search or Maps, with impressions aggregated monthly.

This is **not a keyword ranking API**.

It does not tell you:

```text
we rank #4 for dentist near me
competitor X ranks #2
```

---

# 17. Reviews

GBP APIs support:

```text
list reviews
get review
reply to review
update owner reply
delete owner reply
```

Current review responses contain more information than the assignment dataset.

Conceptual shape:

```json
{
  "name": "accounts/123/locations/456/reviews/789",
  "reviewId": "789",
  "reviewer": {
    "profilePhotoUrl": "https://...",
    "displayName": "Customer Name",
    "isAnonymous": false
  },
  "starRating": "FIVE",
  "comment": "Great experience.",
  "createTime": "2026-09-01T10:20:00Z",
  "updateTime": "2026-09-01T10:20:00Z",
  "reviewReply": {
    "comment": "Thank you for visiting.",
    "updateTime": "2026-09-02T08:00:00Z"
  }
}
```

Current documentation also includes newer review/reply-related fields such as:

- review media items;
- review-reply state;
- policy violation information;
- review-reply URL.

### Reply action

Conceptual request:

```http
PUT /v4/accounts/{accountId}/locations/{locationId}/reviews/{reviewId}/reply
```

Body:

```json
{
  "comment": "Thank you for your feedback."
}
```

### Delete reply

You can delete the **business owner's reply**.

You cannot use this endpoint to delete the customer's review itself.

---

# 18. Safe AI Review Reply Flow

Recommended:

```text
New Review
   ↓
Pub/Sub notification
   ↓
Fetch review
   ↓
AI drafts reply
   ↓
Show user draft
   ↓
User approves
   ↓
GBP reviews.updateReply
   ↓
Audit log
```

Do not:

```text
New Review
   ↓
AI automatically sends reply
without prior specific merchant consent
```

Google's current policy explicitly restricts automated actions without prior specific and express consent.

---

# 19. Media / Photos / Videos

Merchant media API supports:

```text
list
get
create
startUpload
patch metadata
delete
```

Conceptual media resource:

```json
{
  "name": "accounts/123/locations/456/media/abc",
  "mediaFormat": "PHOTO",
  "locationAssociation": {
    "category": "INTERIOR"
  },
  "googleUrl": "https://...",
  "thumbnailUrl": "https://...",
  "createTime": "2026-08-18T11:00:00Z",
  "dimensions": {
    "widthPixels": 1600,
    "heightPixels": 1200
  },
  "insights": {
    "viewCount": "280"
  }
}
```

Media categories can include types such as:

```text
COVER
PROFILE
EXTERIOR
INTERIOR
PRODUCT
AT_WORK
FOOD_AND_DRINK
MENU
COMMON_AREA
ROOMS
TEAMS
ADDITIONAL
```

### Upload flow

```text
Our app
  ↓
startUpload
  ↓
Google returns upload/data reference
  ↓
upload binary
  ↓
create media item
  ↓
media appears on profile after applicable processing/review
```

### Customer media

Customer-contributed media is a separate read-oriented resource.

You can list/get customer media metadata.

You must preserve required attribution.

Do not assume merchant write/delete permissions over customer-submitted media.

---

# 20. Local Posts

GBP supports local post management through documented resources.

Supported concepts include:

```text
STANDARD
EVENT
OFFER
ALERT
```

Posts can contain data such as:

```text
summary
callToAction
createTime
updateTime
scheduledTime
event
state
media
searchUrl
topicType
offer
```

Conceptual post:

```json
{
  "languageCode": "en-US",
  "summary": "Appointments available this weekend.",
  "callToAction": {
    "actionType": "BOOK",
    "url": "https://example.com/book"
  },
  "topicType": "STANDARD"
}
```

Supported actions include:

```text
create
get
list
patch
delete
```

Google's modern Performance API removed the old local-post insights endpoint, so do not design the current performance pipeline around post-insight metrics without re-validating availability.

---

# 21. Place Action Links

Place Actions are URLs customers can use to take an action.

Types include:

```text
APPOINTMENT
ONLINE_APPOINTMENT
DINING_RESERVATION
FOOD_ORDERING
FOOD_DELIVERY
FOOD_TAKEOUT
SHOP_ONLINE
```

Conceptual JSON:

```json
{
  "name": "locations/123/placeActionLinks/456",
  "providerType": "MERCHANT",
  "isEditable": true,
  "uri": "https://example.com/book",
  "placeActionType": "APPOINTMENT",
  "isPreferred": true,
  "createTime": "2026-09-01T00:00:00Z",
  "updateTime": "2026-09-01T00:00:00Z"
}
```

Supported methods:

```text
create
get
list
patch
delete
```

Important distinction:

```text
Place Action API = manages booking/order/reservation LINKS
```

It does **not** mean Google gives your app a detailed CRM table of every booking request.

---

# 22. Business Calls API

For eligible locations, Google's Business Calls API can expose aggregate call insights such as:

```json
{
  "name": "locations/123/businesscallsinsights",
  "metricType": "AGGREGATE_COUNT",
  "aggregateMetrics": {
    "missedCallsCount": 31,
    "answeredCallsCount": 92,
    "hourlyMetrics": [
      {
        "hour": 10,
        "missedCallsCount": 4
      }
    ],
    "weekdayMetrics": []
  }
}
```

Useful possible features:

```text
missed call rate
answered calls
missed calls by hour
missed calls by weekday
```

This is additional to `CALL_CLICKS`.

A call click is not the same as a successfully answered telephone call.

Availability/eligibility should be checked per location.

---

# 23. Notifications / Near-Real-Time Sync

The Notifications API uses Google Cloud Pub/Sub.

High-level setup:

```text
Create Pub/Sub Topic
   ↓
Grant publish permission to:
mybusiness-api-pubsub@system.gserviceaccount.com
   ↓
Configure account NotificationSetting
   ↓
Google publishes events
   ↓
Our subscriber receives event
   ↓
Fetch changed resource
   ↓
Update system
```

Supported current notification concepts include:

```text
GOOGLE_UPDATE
NEW_REVIEW
UPDATED_REVIEW
NEW_CUSTOMER_MEDIA
DUPLICATE_LOCATION
VOICE_OF_MERCHANT_UPDATED
```

This enables efficient event-driven refresh.

Example:

```text
NEW_REVIEW
   ↓
fetch specific review
   ↓
save/use permitted temporary data
   ↓
recompute review features
   ↓
generate recommendation
```

Do not poll all reviews every minute.

---

# 24. Q&A — Important Current Status

Do **not** build a new integration around the old Q&A endpoints.

Google discontinued the My Business Q&A API on:

```text
3 November 2025
```

You can no longer read or post questions/answers through that API.

Older v4 documentation pages may still list Q&A resources, so a developer who only reads the older reference index can be misled.

The current deprecation schedule must take precedence.

---

# 25. Verifications / Voice of Merchant

The Verifications API provides methods such as:

```text
fetchVerificationOptions
getVoiceOfMerchantState
verify
list verifications
complete pending verification
```

Example Voice of Merchant response:

```json
{
  "hasVoiceOfMerchant": true,
  "hasBusinessAuthority": true
}
```

If not controlled/verified, the response can contain a recommended next action.

Use this to determine whether:

```text
profile edits are likely to propagate
ownership/verification attention is required
```

Verification should only be initiated when directly requested by the business owner.

---

# 26. Google Updates

Google can suggest/update business data.

Useful signals include:

```text
hasGoogleUpdated
GOOGLE_UPDATE notification
getGoogleUpdated
Google-updated attributes
```

Recommended product behavior:

```text
Google update detected
     ↓
Fetch merchant value
+
Google-updated value
     ↓
Show difference
     ↓
Merchant reviews
     ↓
Merchant chooses action
```

Do not automatically revert Google's updates.

Current policy specifically prohibits automatically reverting Google-made changes.

---

# 27. Category-Specific Data

Not every location supports the same features.

Examples:

### Food businesses

Potentially:

```text
food menus
food ordering links
delivery/takeout links
menu interactions
food orders performance metrics
```

### Service businesses

Potentially:

```text
service items
service area
appointment links
```

### Lodging

Has lodging-specific capabilities/resources.

### Health-related profiles

Some old health/insurance resources have been deprecated, so current availability must be checked rather than building against legacy methods blindly.

Your app should therefore use capability detection:

```text
Location Metadata
Category
Available attributes
Available place-action types
API eligibility
```

instead of hard-coded industry screens.

---

# 28. What Our Product Can Potentially Let a User Do

## Core profile

| Action | Possible through GBP APIs? |
|---|---:|
| Read business name/title | Yes |
| Update supported business information | Yes |
| Read/update website | Yes |
| Read/update phone | Yes |
| Read/update supported address fields | Yes |
| Read/update categories | Yes |
| Read/update regular hours | Yes |
| Read/update special hours | Yes |
| Read/update service area | Yes |
| Read/update description | Yes |
| Read/update supported services | Yes |
| Read/update supported attributes | Yes |
| Read open/closed status | Yes |
| Update supported open-info fields | Yes, subject to rules/permissions |
| Read Google-updated profile | Yes |
| Auto-revert Google updates | **No — prohibited** |

## Reviews

| Action | Possible? |
|---|---:|
| List reviews | Yes |
| Read review text/rating | Yes |
| Read owner reply | Yes |
| Create owner reply | Yes |
| Update owner reply | Yes |
| Delete owner reply | Yes |
| Delete customer review | No |
| AI draft review reply | Yes in our app |
| Automatically publish AI reply without prior specific consent | No |

## Media

| Action | Possible? |
|---|---:|
| List merchant media | Yes |
| Get media metadata | Yes |
| Upload merchant photo/video | Yes, subject to API/media requirements |
| Delete merchant media | Yes where allowed |
| Read customer media metadata | Yes |
| Delete arbitrary customer media | Not via merchant media CRUD |

## Posts

| Action | Possible? |
|---|---:|
| List posts | Yes |
| Create supported local post | Yes |
| Update supported post | Yes |
| Delete post | Yes |
| Add CTA | Yes where supported |
| Add event/offer fields | Yes where supported |
| Depend on modern Performance API for post insights | No; old post-insights endpoint was removed from the modern performance migration |

## Action links

| Action | Possible? |
|---|---:|
| Read appointment/order links | Yes |
| Create merchant action link | Yes where supported |
| Update link | Yes |
| Delete link | Yes |
| Fetch every actual appointment/customer record | No, not from Place Actions |

## Verification

| Action | Possible? |
|---|---:|
| Check Voice of Merchant | Yes |
| Fetch verification options | Yes |
| Start verification | Yes, owner-requested workflow |
| Complete pending verification | Supported where applicable |

---

# 29. Assignment Dataset vs Google — High-Level Mapping

The supplied data is **mixed**.

Some files closely mirror GBP API data.

Others are app-derived or external.

| Supplied file | GBP source? | Assessment |
|---|---|---|
| `locations.csv` | Mostly yes | Core fields map to Business Information; some are internal/derived |
| `location_hours.csv` | Yes | Derived from `regularHours`; sample simplifies Google's richer hours model |
| `location_daily_kpis.csv` | **Yes, very close** | Maps strongly to Performance DailyMetric |
| `location_search_terms_monthly.csv` | **Yes, very close** | Maps to monthly search-keyword impressions |
| `attribute_catalog.csv` | Mostly yes conceptually | Google provides dynamic attributes by category/country; sample normalizes/group labels |
| `location_attributes.csv` | Yes | Maps to location attribute values |
| `location_media_summary.csv` | **Derived from Google media** | Google returns media items; summary counts must be calculated |
| `reviews.csv` | Yes | Subset of Google Review resource |
| `review_replies.csv` | Yes | Subset of ReviewReply |
| `posts.csv` | Yes | Subset of LocalPost |
| `booking_requests.csv` | **No** | Detailed customer booking records are not Performance API output |
| `tracked_keywords.csv` | **No** | App/rank-tracker configuration |
| `keyword_rank_weekly.csv` | **No** | Requires rank/SERP tracking source |
| `competitor_ranks_weekly.csv` | **No** | Requires external competitive/rank source |

---

# 30. Detailed Mapping — `locations.csv`

Supplied columns:

```text
location_id
gbp_location_id
store_code
name
primary_category
additional_categories
city
state
postal_code
latitude
longitude
phone
website_url
description
description_length
opened_on
verified
open_status
```

Mapping:

| Supplied field | Google equivalent | Notes |
|---|---|---|
| `location_id` | None | Internal application identifier |
| `gbp_location_id` | `Location.name` / location resource ID | Google form: `locations/{locationId}` |
| `store_code` | `storeCode` | Direct |
| `name` | `title` | Direct concept |
| `primary_category` | `categories.primaryCategory` | Direct |
| `additional_categories` | `categories.additionalCategories[]` | Direct, sample flattens |
| `city` | `storefrontAddress.locality` | Direct-ish |
| `state` | `storefrontAddress.administrativeArea` | Direct-ish |
| `postal_code` | `storefrontAddress.postalCode` | Direct |
| `latitude` | `latlng.latitude` | Conditional; Google notes lat/lng is not always returned |
| `longitude` | `latlng.longitude` | Conditional |
| `phone` | `phoneNumbers.primaryPhone` | Direct |
| `website_url` | `websiteUri` | Direct |
| `description` | `profile.description` | Direct |
| `description_length` | None | Derived by your code |
| `opened_on` | `openInfo.openingDate` | Direct concept if supplied |
| `verified` | `metadata.hasVoiceOfMerchant` / Verifications state | Better treated as derived state, not simply a universal raw boolean |
| `open_status` | `openInfo.status` | `OPEN`, `CLOSED_PERMANENTLY`, `CLOSED_TEMPORARILY` |

Google exposes more fields than this CSV.

---

# 31. Detailed Mapping — `location_hours.csv`

Supplied:

```text
location_id
day_of_week
open_time
close_time
```

Google source:

```text
Location.regularHours.periods[]
```

But Google supports more complex cases:

```text
multiple open periods in one day
overnight periods
special/holiday hours
additional/more-hours types
```

The assignment CSV simplifies this.

---

# 32. Detailed Mapping — `location_daily_kpis.csv`

Supplied:

```text
location_id
date
impressions_maps_desktop
impressions_maps_mobile
impressions_search_desktop
impressions_search_mobile
website_clicks
call_clicks
direction_requests
conversations
bookings
```

These align very closely with the Performance API.

| Assignment field | Google DailyMetric |
|---|---|
| `impressions_maps_desktop` | `BUSINESS_IMPRESSIONS_DESKTOP_MAPS` |
| `impressions_maps_mobile` | `BUSINESS_IMPRESSIONS_MOBILE_MAPS` |
| `impressions_search_desktop` | `BUSINESS_IMPRESSIONS_DESKTOP_SEARCH` |
| `impressions_search_mobile` | `BUSINESS_IMPRESSIONS_MOBILE_SEARCH` |
| `website_clicks` | `WEBSITE_CLICKS` |
| `call_clicks` | `CALL_CLICKS` |
| `direction_requests` | `BUSINESS_DIRECTION_REQUESTS` |
| `conversations` | `BUSINESS_CONVERSATIONS` |
| `bookings` | `BUSINESS_BOOKINGS` |

Important:

`BUSINESS_BOOKINGS` represents bookings attributed through supported Google booking integrations; it is an aggregate performance metric.

It is not a detailed booking database.

Google also has performance metrics not present in this sample, such as:

```text
BUSINESS_FOOD_ORDERS
BUSINESS_FOOD_MENU_CLICKS
```

where applicable.

---

# 33. Detailed Mapping — `location_search_terms_monthly.csv`

Supplied:

```text
location_id
year_month
search_term
impressions
```

Google:

```json
{
  "searchKeyword": "dentist near me",
  "insightsValue": {
    "value": "123"
  }
}
```

or:

```json
{
  "searchKeyword": "rare query",
  "insightsValue": {
    "threshold": "15"
  }
}
```

The sample simplifies Google's `value OR threshold` behavior into an `impressions` field.

---

# 34. Detailed Mapping — Attributes

## `attribute_catalog.csv`

Supplied:

```text
attribute_id
attribute_name
attribute_group
applies_to_category
value_type
```

Google provides an attribute catalog conditioned on category/country.

Google concepts include:

```text
attribute ID/name
display strings
value type
supported category/country
possible enum values
```

The sample's `attribute_group` is likely a simplified/normalized application-level grouping rather than a guarantee of Google's raw response shape.

---

## `location_attributes.csv`

Supplied:

```text
location_id
attribute_id
value
```

Maps naturally to Google listing attributes.

Google attributes can contain:

```text
boolean values
enum values
repeated enum values
URLs / other supported value types
```

Production schema should be more flexible than a single generic scalar string.

---

# 35. Detailed Mapping — `location_media_summary.csv`

Supplied:

```text
location_id
photo_count
interior_photo_count
exterior_photo_count
team_photo_count
video_count
has_profile_photo
has_cover_photo
last_photo_uploaded_on
```

Google does **not** primarily return this exact summary row.

Instead it returns individual media items.

Your system calculates:

```text
photo_count =
COUNT(media where mediaFormat == PHOTO)

video_count =
COUNT(media where mediaFormat == VIDEO)

interior_photo_count =
COUNT(PHOTO where category == INTERIOR)

has_profile_photo =
EXISTS(category == PROFILE)

last_photo_uploaded_on =
MAX(createTime)
```

Therefore this assignment file is:

```text
Google source data
      ↓
our aggregation
      ↓
media summary
```

---

# 36. Detailed Mapping — `reviews.csv`

Supplied:

```text
review_id
location_id
reviewer_name
rating
review_text
created_at
```

Maps to Google:

```text
reviewId
location resource relationship
reviewer.displayName
starRating
comment
createTime
```

Google currently exposes additional review data that the sample omits, such as:

```text
reviewer profile photo
anonymous indicator
update time
review media
owner reply embedded with review
reply state / moderation-related data
reply URL
```

---

# 37. Detailed Mapping — `review_replies.csv`

Supplied:

```text
review_id
reply_text
replied_at
```

Maps to:

```text
review.reviewReply.comment
review.reviewReply.updateTime
```

Current Google review objects can expose additional reply-related state.

---

# 38. Detailed Mapping — `posts.csv`

Supplied:

```text
post_id
location_id
post_type
summary
cta_type
published_on
```

Google LocalPost provides significantly more data.

Possible structures include:

```text
resource name
language
summary
CTA object
create time
update time
scheduled time
recurrence-related fields
event
state
media
search URL
topic type
alert
offer
```

The sample is a simplified subset.

---

# 39. `booking_requests.csv` — NOT Direct GBP Data

Supplied:

```text
booking_id
location_id
customer_name
service
requested_for_date
status
source
created_at
```

Possible sources include:

```text
CRM
practice-management system
appointment scheduler
website booking engine
Reserve-with-Google partner system
POS
phone workflow
manual/walk-in system
```

GBP Performance gives aggregate:

```text
BUSINESS_BOOKINGS
```

but does not expose this supplied per-customer booking table through the standard Performance API.

The fact that the assignment contains sources such as:

```text
website
google_profile
phone
walk_in
```

also demonstrates that this is a broader business operations dataset rather than purely Google API data.

---

# 40. `tracked_keywords.csv` — NOT GBP API Data

Supplied:

```text
keyword_id
location_id
keyword
search_intent
device
tracking_started_on
```

This is an application/rank-tracking configuration table.

GBP search keyword impressions tell you:

```text
which queries surfaced your own business
+
monthly impressions
```

They do **not** provide:

```text
custom tracked keyword IDs
search intent labels
tracking device configuration
ranking tracking start date
```

Those are created by your own product or a third-party SEO system.

---

# 41. `keyword_rank_weekly.csv` — NOT GBP API Data

Supplied:

```text
keyword_id
location_id
week_start
rank_absolute
rank_in_local_pack
found
result_url
```

Google Business Profile management/performance APIs do **not** provide a local rank-tracking endpoint returning:

```text
rank #1, #2, #8...
local pack position
found/not-found per custom tracked keyword
```

This needs a separate rank-tracking source.

Possible architecture:

```text
GBP APIs
   +
Rank Tracker / SERP Provider
   ↓
Unified location intelligence model
```

---

# 42. `competitor_ranks_weekly.csv` — NOT GBP API Data

Supplied:

```text
keyword_id
week_start
competitor_name
competitor_place_id
rank_absolute
review_count
average_rating
photo_count
is_claimed
```

This is not a normal GBP owner API response.

You need a separate competitive-data source.

Potential options depend on exact use case and terms:

```text
local SEO/rank-tracking provider
permitted SERP/rank provider
other Google Maps Platform products where relevant
other licensed business-data source
```

Do not assume Business Profile OAuth gives access to competitors' private/profile-management data.

GBP access only lets you query profiles the authenticated user is authorized to manage.

---

# 43. Data in Google That the Assignment Does NOT Include

The assignment is intentionally simplified.

Additional data/capabilities potentially available include:

## Account/access

```text
account type
role
permission level
management context
```

## Core location

```text
language code
additional phone numbers
full structured address
special hours
more hours
service area
labels
relationship data
service items
place ID
Maps URI
new-review URI
pending edits
Google updates
capability/eligibility metadata
```

## Reviews

```text
review update time
reviewer profile-photo URL
anonymity
review media
reply moderation/status data
review-reply URL
```

## Media

```text
Google media URL
thumbnail
dimensions
individual media category
create time
view count / media insight fields
attribution
```

## Posts

```text
state
media
event details
offer details
search URL
scheduling
recurrence-related data
update time
```

## Verification

```text
Voice of Merchant
business authority
verification options
verification records
recommended next verification/control action
```

## Action links

```text
appointment links
online appointments
restaurant reservations
food ordering
delivery
takeout
shop online
```

## Calls

For eligible locations:

```text
answered calls
missed calls
missed calls by hour
missed calls by weekday
```

## Events

Pub/Sub notification events:

```text
new review
updated review
new customer media
Google update
duplicate-location change
Voice of Merchant change
```

---

# 44. Recommended Unified Internal Schema

Do not store the raw Google JSON as the only application model.

Normalize into provider-independent internal entities.

```text
organizations
connections
external_accounts
locations

location_snapshots
location_categories
location_hours
location_special_hours
location_attributes
location_services

performance_daily
search_terms_monthly

reviews
review_replies
review_features

media_items
media_features

posts
place_action_links

verification_state
google_update_events

tracked_keywords
keyword_ranks
competitor_observations

booking_requests

recommendations
recommendation_actions
recommendation_outcomes
```

Maintain mapping fields:

```text
internal_location_id
google_location_resource_name
google_place_id
store_code
```

---

# 45. Provider Separation

Recommended conceptual architecture:

```text
                         OUR LOCATION
                              │
       ┌──────────────────────┼───────────────────────┐
       │                      │                       │
       ▼                      ▼                       ▼
     GOOGLE                 SEO DATA             BUSINESS DATA
       │                      │                       │
GBP Business Info       Rank provider             CRM
GBP Performance         Competitors               Booking
GBP Reviews             Keyword tracking          POS
GBP Media                                        Call tracking
GBP Posts                                        Website analytics
       │                      │                       │
       └──────────────────────┼───────────────────────┘
                              ▼
                       Feature Engine
                              ▼
                    Recommendation Engine
```

This prevents the architectural mistake of assuming Google is the source of every useful local-business signal.

---

# 46. Recommended Sync Frequencies

Subject to policy, quota, data availability and product requirements:

| Data | Suggested trigger |
|---|---|
| New/updated reviews | Pub/Sub event |
| Customer media | Pub/Sub event |
| Google updates | Pub/Sub event |
| VOM status | Event / relevant workflow |
| Location core profile | Initial sync + periodic/change-driven |
| Attributes | Initial + change/category refresh |
| Performance daily | Daily |
| Search terms | Monthly / scheduled |
| Posts | Initial + after user actions + periodic |
| Merchant media | Initial + after user actions + periodic |
| Place-action links | Initial + after user actions |
| Rank tracking | External scheduled process |
| Competitors | External scheduled process |
| CRM bookings | CRM/webhook/batch source |

Do not refresh everything on every page load.

---

# 47. Recommended Multi-User Production Architecture

```text
                       User
                        │
             Connect Google Profile
                        │
                        ▼
                 OAuth Service
                        │
                        ▼
              Connection Registry
                        │
             encrypted refresh token
                        │
                        ▼
                 Sync Scheduler
                        │
              ┌─────────┴─────────┐
              ▼                   ▼
         Batch Jobs          Pub/Sub Events
              │                   │
              └─────────┬─────────┘
                        ▼
                 Ingestion Queue
                        │
                        ▼
                  Google Clients
                        │
                        ▼
                  Validation Layer
                        │
                        ▼
                Normalized Storage
                        │
                        ▼
                  Feature Engine
                        │
             ┌──────────┴──────────┐
             ▼                     ▼
           Rules                ML / AI
             │                     │
             └──────────┬──────────┘
                        ▼
               Recommendation Store
                        │
                        ▼
                       API
                        │
                        ▼
                  User Dashboard
```

---

# 48. API Call / Queue Strategy for Scale

Do not do this:

```text
User opens page
   ↓
Call 15 Google endpoints
   ↓
Wait
   ↓
Run AI
   ↓
Return page
```

Use:

```text
Background sync
   ↓
Store latest permitted state/features
   ↓
Generate recommendation
   ↓
User opens page
   ↓
Instant DB/cache response
```

For refresh:

```text
User clicks Refresh
   ↓
enqueue sync
   ↓
show latest available state
   ↓
update when job finishes
```

---

# 49. Current Standard Quota Considerations

Google currently documents standard limits including roughly:

```text
Business Information:
300 QPM default requests

Create Location:
300 QPD

SearchGoogleLocation:
300 QPD

Update Location:
10,000 QPD

Edits:
10/minute per profile

Account Management:
300 QPM

Performance:
300 QPM

Verifications:
300 QPM

Lodging:
300 QPM

Place Actions:
300 QPM

Notifications:
300 QPM
```

Implement:

```text
queue
rate limiting
per-account/per-profile pacing
retry
exponential backoff
jitter
dead-letter queue
idempotency
```

Do not rely on unlimited parallel API calls.

---

# 50. Recommended Write-Action Architecture

Every profile-modifying action should be represented internally.

Example:

```json
{
  "action_id": "act_981",
  "location_id": "loc_123",
  "action_type": "REPLY_TO_REVIEW",
  "source": "AI_RECOMMENDATION",
  "requested_by_user_id": "user_55",
  "approval_status": "APPROVED",
  "payload": {
    "review_id": "review_77",
    "reply": "Thank you for your feedback."
  },
  "google_execution_status": "PENDING"
}
```

Execution:

```text
Recommendation
     ↓
User approval
     ↓
Action record
     ↓
Queue
     ↓
Google API
     ↓
Success / failure
     ↓
Audit log
```

This provides:

- explicit consent evidence;
- retries;
- accountability;
- rollback awareness where supported;
- model-learning history.

---

# 51. AI + GBP Management

AI can safely be used as a recommendation/drafting layer.

Examples:

```text
AI drafts review reply
AI drafts post
AI suggests profile-description improvement
AI identifies missing attributes
AI explains performance decline
AI suggests photo categories to improve
AI recommends service/profile changes
```

But the AI should not have unrestricted direct credentials.

Recommended:

```text
AI
 ↓
Structured proposed action
 ↓
Policy validation
 ↓
User approval
 ↓
Action service
 ↓
Google API
```

The action service, not the LLM, holds credentials.

---

# 52. Example Structured AI Proposal

```json
{
  "recommendation_type": "REVIEW_REPLY",
  "location_id": "loc_123",
  "evidence": {
    "review_id": "review_77",
    "rating": 2,
    "topic": "waiting_time"
  },
  "proposed_action": {
    "operation": "UPDATE_REVIEW_REPLY",
    "draft": "Thank you for sharing this. We are reviewing the delay you experienced."
  },
  "requires_user_approval": true
}
```

Only after approval:

```text
Action Service
  ↓
reviews.updateReply
```

---

# 53. What Google Does NOT Give You Through GBP OAuth

Do not expect GBP APIs to provide:

```text
every competitor's managed profile data
your rank for arbitrary tracked keywords
competitor rank history
local-pack rank history
custom search-intent classifications
customer CRM records
walk-in records
phone booking records
detailed website lead records
revenue/profit
conversion value
ad campaign data
full organic SEO ranking data
private competitor data
```

Those require separate integrations/data sources.

---

# 54. Core Conclusion About the Supplied Dataset

The supplied dataset is **not simply a dump of Google Business Profile API data**.

It is better described as:

```text
GBP core/profile data
+
GBP performance data
+
GBP review/post/media data
+
derived aggregates
+
SEO/rank-tracking data
+
competitor intelligence
+
booking/operational data
```

Specifically:

### Strong direct GBP correspondence

```text
locations.csv
location_hours.csv
location_daily_kpis.csv
location_search_terms_monthly.csv
location_attributes.csv
reviews.csv
review_replies.csv
posts.csv
```

### GBP-derived aggregation

```text
location_media_summary.csv
attribute_catalog.csv (conceptually Google-backed but normalized)
```

### External / product-owned data

```text
tracked_keywords.csv
keyword_rank_weekly.csv
competitor_ranks_weekly.csv
booking_requests.csv
```

This distinction should be reflected in both the product architecture and the take-home solution.

---

# 55. Recommended Integration Plan

## Phase 1 — Read-only connection

Build:

```text
OAuth
Accounts
Locations
Business Information
Performance
Search keywords
Reviews
Media
Posts
Attributes
```

Goal:

```text
Connect → Sync → Analyze → Recommend
```

This reduces policy/action risk initially.

---

## Phase 2 — User-approved write actions

Add:

```text
reply to review
edit profile
update hours
update attributes
create/edit/delete posts
upload/manage merchant media
manage place-action links
```

Every write action should require clear user intent/approval.

---

## Phase 3 — Event-driven automation

Add:

```text
Pub/Sub
new review event
updated review event
customer media event
Google update event
VOM event
```

Use events to trigger analysis, not unrestricted automatic profile mutation.

---

## Phase 4 — Additional providers

Add:

```text
rank tracker
competitor intelligence provider
CRM / booking systems
call tracking
website analytics
POS / revenue
```

This produces the complete intelligence dataset needed for strong recommendations.

---

# 56. Official Documentation Used

Primary official references:

### Overview

https://developers.google.com/my-business

https://developers.google.com/my-business/content/overview

### Prerequisites / API access

https://developers.google.com/my-business/content/prereqs

### OAuth

https://developers.google.com/my-business/content/oauth-overview

https://developers.google.com/my-business/content/implement-oauth

https://developers.google.com/my-business/content/oauth-setup

### Policies

https://developers.google.com/my-business/content/policies

### Quotas

https://developers.google.com/my-business/content/limits

### Business Information

https://developers.google.com/my-business/reference/businessinformation/rest/v1/locations

https://developers.google.com/my-business/reference/businessinformation/rest/v1/accounts.locations

### Attributes

https://developers.google.com/my-business/content/attributes

### Performance

https://developers.google.com/my-business/reference/performance/rest

https://developers.google.com/my-business/reference/performance/rest/v1/locations/fetchMultiDailyMetricsTimeSeries

https://developers.google.com/my-business/reference/performance/rest/v1/locations.searchkeywords.impressions.monthly/list

https://developers.google.com/my-business/content/performance/change-log

### Reviews

https://developers.google.com/my-business/content/review-data

https://developers.google.com/my-business/reference/rest/v4/accounts.locations.reviews

### Posts

https://developers.google.com/my-business/content/posts-data

https://developers.google.com/my-business/reference/rest/v4/accounts.locations.localPosts

### Media

https://developers.google.com/my-business/reference/rest/v4/accounts.locations.media

https://developers.google.com/my-business/reference/rest/v4/accounts.locations.media.customers

### Notifications

https://developers.google.com/my-business/content/notification-setup

https://developers.google.com/my-business/reference/notifications/rest/v1/NotificationSetting

### Verifications

https://developers.google.com/my-business/reference/verifications/rest/v1/locations

### Place Actions

https://developers.google.com/my-business/reference/placeactions/rest/v1/locations.placeActionLinks

### Business Calls

https://developers.google.com/my-business/reference/businesscalls/rest/v1/locations.businesscallsinsights/list

### Deprecations / Q&A

https://developers.google.com/my-business/content/sunset-dates

https://developers.google.com/my-business/content/qanda/change-log

---

# 57. Final Developer Summary

The production design should be:

```text
USER
 ↓
GOOGLE OAUTH
 ↓
AUTHORIZED GBP ACCOUNT
 ↓
GBP APIS
 ↓
NORMALIZATION
 ↓
FEATURE ENGINE
 ↓
RULES + ML + AI
 ↓
RECOMMENDATIONS
 ↓
USER APPROVAL
 ↓
SUPPORTED GBP WRITE ACTION
 ↓
AUDIT / OUTCOME
```

And the overall data platform should be:

```text
GBP APIs
   +
External SEO/rank data
   +
CRM/booking data
   +
Business-owned data
        ↓
Unified Location Intelligence Layer
        ↓
Recommendation Engine
```

The most important implementation principle is:

> **Treat Google Business Profile as a major source and action surface, not as the only source of location intelligence.**

Google gives strong first-party profile, engagement, review, media, post, attribute and performance data, but the supplied assignment also relies on external ranking, competitor and booking information that must come from other systems.
