"""The ten demo businesses, and the exact shape of what is wrong with each.

An archetype is two things: an identity (name, trade, city, the words customers write
about it) and a `Problems` record, which is a declaration of which checks the generated
data should fail. Every field on `Problems` defaults to healthy, so an archetype only
states its own faults and reads as a short diagnosis.

The spread is deliberate. One profile's reputation is the disaster, one's visibility has
collapsed, one is operationally broken, one has no content, and the rest mix. Scores are
aimed at the poor (under 50) and fair (50-74) bands, never at ten identical catastrophes.
"""

from __future__ import annotations

from dataclasses import dataclass, field

WEEK = ("MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY")
FULL_WEEK = (*WEEK, "SATURDAY", "SUNDAY")


@dataclass(frozen=True)
class BookingMix:
    """How the last 90 days of appointment requests ended up.

    `new_stale` are requests still marked new, all created more than the three-day reply
    wait ago; `expired` is how many of those asked for a date that has already passed.
    The rest are the statuses the booking system settled on.
    """

    new_stale: int = 2
    expired: int = 0
    confirmed: int = 8
    completed: int = 22
    cancelled: int = 3
    no_show: int = 1

    @property
    def total(self) -> int:
        return self.new_stale + self.confirmed + self.completed + self.cancelled + self.no_show


@dataclass(frozen=True)
class Problems:
    """Every knob the generator reads. Defaults describe a healthy profile."""

    # ---- profile -------------------------------------------------------------------
    phone: bool = True
    website: str | None = "https"  # "https" | "http" | None
    address_complete: bool = True
    pin: bool = True
    additional_categories: int = 3
    verified: bool = True
    temporarily_closed: bool = False
    opening_date: bool = True
    # good | thin (long enough but says nothing) | short | missing | stuffed | long
    description: str = "good"
    name_stuffed: bool = False
    logo: bool = True
    cover: bool = True
    open_days: tuple[str, ...] = WEEK
    odd_hours: bool = False
    # Share of the category's attribute catalog that carries an answer.
    attribute_share: float = 0.85
    accessibility_answered: bool = True
    # Attributes forced to an explicit "no", by catalog name.
    attributes_denied: tuple[str, ...] = ()

    # ---- reputation ----------------------------------------------------------------
    # Star mix as counts of 1..5 stars, for the last 90 days and the 90 before that.
    recent_mix: tuple[int, int, int, int, int] = (0, 1, 2, 7, 18)
    prior_mix: tuple[int, int, int, int, int] = (0, 1, 2, 8, 20)
    newest_review_days: int = 4
    recent_last_30: int = 9
    reply_share: float = 0.92
    critical_reply_share: float = 1.0
    reply_delay_days: int = 2
    # Median review count of the rivals seen on this location's keywords.
    competitor_reviews: int = 90

    # ---- visibility ----------------------------------------------------------------
    # (keyword, search intent, rank pattern). Patterns: top pack near mid lost drop gone.
    keyword_plan: tuple[tuple[str, str, str], ...] = ()
    # Terms that lost at least half their impressions against the month before.
    losing_terms: int = 0
    # How much stronger the rivals look than us, as a multiplier on our own figures.
    rival_strength: float = 1.0

    # ---- operations ----------------------------------------------------------------
    bookings: BookingMix = field(default_factory=BookingMix)
    weekend_requests: int = 0
    dominant_channel_share: float = 0.55
    unlisted_services: tuple[str, ...] = ()
    google_bookings_zero: bool = False
    lead_collapse: bool = False

    # ---- performance ---------------------------------------------------------------
    impressions_base: int = 140  # daily impressions in the previous window
    impressions_drop: float = 0.0
    calls_drop: float = 0.0
    directions_drop: float = 0.0
    clicks_drop: float = 0.0
    maps_shift: float = 0.0  # change in the Maps share of impressions, in points
    mobile_shift: float = 0.0
    zero_action_streak: int = 0
    missing_days: int = 0

    # ---- content -------------------------------------------------------------------
    photos: int = 44
    photo_types: tuple[int, int, int] = (16, 12, 9)  # interior, exterior, team
    videos: int = 2
    photo_age_days: int = 18
    posts_90d: int = 10
    last_post_days: int = 7
    post_types: tuple[str, ...] = ("standard", "offer", "event")
    post_cta_share: float = 0.9


@dataclass(frozen=True)
class Archetype:
    key: str
    name: str
    industry: str
    city: str
    state: str
    postal_code: str
    latitude: float
    longitude: float
    phone: str
    website: str
    primary_category: str
    extra_categories: tuple[str, ...]
    description: str
    services: tuple[str, ...]
    search_terms: tuple[str, ...]
    booking_services: tuple[str, ...]
    rivals: tuple[str, ...]
    complaints: tuple[str, ...]
    mixed: tuple[str, ...]
    praise: tuple[str, ...]
    posts: tuple[str, ...]
    # Category-specific attributes added to the shared base catalog, as (name, group).
    attributes: tuple[tuple[str, str], ...]
    headline_problem: str
    expected_grade: str
    # The categories this archetype exists to drag down — the story the demo tells about
    # it. Not simply its two lowest scores: reputation and performance bottom out easily
    # under the scoring policy, while a notice-heavy category like visibility never falls
    # far however badly it does.
    failing: tuple[str, ...]
    problems: Problems

    @property
    def location(self) -> str:
        return f"{self.city}, {self.state}"


# The attributes Google offers almost every local business, used as the base catalog for
# each archetype's primary category. Category-specific ones are added per archetype.
BASE_ATTRIBUTES: tuple[tuple[str, str], ...] = (
    ("wheelchair_accessible_entrance", "accessibility"),
    ("wheelchair_accessible_restroom", "accessibility"),
    ("wheelchair_accessible_parking", "accessibility"),
    ("has_onsite_parking", "accessibility"),
    ("free_street_parking", "accessibility"),
    ("accepts_credit_cards", "payments"),
    ("accepts_debit_cards", "payments"),
    ("accepts_nfc_mobile_payments", "payments"),
    ("has_restroom", "amenities"),
    ("gender_neutral_restroom", "amenities"),
    ("wifi_available", "amenities"),
    ("identifies_as_women_owned", "identity"),
    ("identifies_as_veteran_owned", "identity"),
    ("lgbtq_friendly", "identity"),
    ("appointment_required", "planning"),
    ("online_appointments", "planning"),
    ("saturday_appointments", "planning"),
    ("evening_appointments", "planning"),
)


ARCHETYPES: tuple[Archetype, ...] = (
    Archetype(
        key="riverside-grill",
        name="Riverside Grill",
        industry="Restaurant",
        city="Austin",
        state="TX",
        postal_code="78702",
        latitude=30.2612,
        longitude=-97.7275,
        phone="+1-512-555-0188",
        website="https://riversidegrill.example.com",
        primary_category="Restaurant",
        extra_categories=("American restaurant", "Bar", "Steak house"),
        description=(
            "Riverside Grill is a wood-fire kitchen on the east bank in Austin, serving "
            "dry-aged steaks, gulf fish and a short list of Texas wines. We have been "
            "open since 2014 and take walk-ins as well as reservations for parties up to "
            "twelve. The patio is dog friendly and the bar pours local draft until "
            "midnight on weekends. Private dining is available upstairs for groups."
        ),
        services=("Dinner service", "Private dining", "Patio seating", "Weekend brunch"),
        search_terms=(
            "steakhouse east austin",
            "restaurant near me",
            "dinner reservations austin",
            "patio dining austin",
            "best steak austin",
            "bar with food austin",
            "riverside grill",
            "late night food austin",
        ),
        booking_services=("Dinner service", "Private dining", "Weekend brunch"),
        rivals=("Lonestar Chophouse", "The Colorado Room", "Barton Fire Kitchen"),
        complaints=(
            "Waited fifty minutes for a table we had booked, then another half hour for "
            "drinks. Nobody apologised.",
            "The steak came out grey and cold. Sent it back and the replacement was worse.",
            "Charged twice on the card and it took three phone calls to get the second "
            "charge reversed.",
            "Bathroom was out of order and the floor by the bar was sticky all evening.",
            "Server was short with us the whole night and sighed when we asked about the "
            "specials.",
            "Booked for a birthday, arrived to find the reservation had been given away.",
        ),
        mixed=(
            "Food was decent but the service is a coin toss depending on who you get.",
            "Good patio, slow kitchen. Fine if you are not in a hurry.",
            "Prices have gone up and portions have gone down since last year.",
        ),
        praise=(
            "The dry-aged ribeye is genuinely excellent and the patio at sunset is hard "
            "to beat.",
            "Bartender made us a proper old fashioned and the kitchen sent out a birthday "
            "dessert unprompted.",
            "Great spot for a group. Upstairs room was quiet enough to actually talk.",
            "Gulf snapper was cooked perfectly and the wine list is short but well chosen.",
        ),
        posts=(
            "Wood-fire dry-aged ribeye is on the board this week alongside gulf snapper.",
            "The patio is open late on Fridays with local drafts until midnight.",
            "Private dining upstairs is taking bookings for the holidays.",
        ),
        attributes=(
            ("serves_beer", "amenities"),
            ("serves_wine", "amenities"),
            ("outdoor_seating", "amenities"),
            ("accepts_reservations", "planning"),
            ("good_for_groups", "planning"),
            ("dogs_allowed_outside", "amenities"),
        ),
        headline_problem="Rating down to 2.7, 40+ complaints unanswered, no hours posted",
        expected_grade="poor",
        failing=("reputation", "content"),
        problems=Problems(
            # Reputation is the disaster: a collapsing rating nobody answers.
            recent_mix=(18, 10, 5, 2, 2),
            prior_mix=(4, 3, 5, 7, 12),
            newest_review_days=5,
            recent_last_30=2,
            reply_share=0.12,
            critical_reply_share=0.05,
            reply_delay_days=21,
            competitor_reviews=320,
            # Content was abandoned when the reviews turned: four photos, nothing posted.
            photos=4,
            photo_types=(0, 0, 0),
            videos=0,
            photo_age_days=214,
            posts_90d=0,
            last_post_days=0,
            post_types=(),
            post_cta_share=0.0,
            logo=False,
            cover=False,
            # The listing is tired too: keyword-bait description, half the fields blank.
            description="stuffed",
            verified=False,
            temporarily_closed=True,
            address_complete=False,
            additional_categories=1,
            opening_date=False,
            pin=False,
            attribute_share=0.3,
            accessibility_answered=False,
            open_days=(),  # the hours were lost in an agency handover and never re-entered
            keyword_plan=(
                ("riverside grill", "general", "gone"),
                ("steakhouse east austin", "general", "slip"),
                ("restaurant near me", "general", "mid"),
                ("dinner reservations austin", "general", "near"),
                ("best steak austin", "general", "lost"),
                ("late night food austin", "general", "gone"),
                ("patio dining austin", "general", "gone"),
                ("weekend brunch austin", "general", "gone"),
                ("private dining austin", "general", "near"),
            ),
            losing_terms=2,
            rival_strength=3.0,
            bookings=BookingMix(new_stale=16, expired=10, confirmed=2, completed=6, cancelled=7,
                                no_show=5),
            weekend_requests=10,
            dominant_channel_share=0.97,
            unlisted_services=("Birthday catering", "Chef's table"),
            google_bookings_zero=True,
            lead_collapse=True,
            impressions_base=260,
            impressions_drop=0.39,
            calls_drop=0.52,
            directions_drop=0.46,
            clicks_drop=0.54,
            maps_shift=0.12,
            zero_action_streak=3,
            missing_days=3,
        ),
    ),
    Archetype(
        key="ironclad-strength",
        name="Ironclad Strength Gym Denver",
        industry="Gym",
        city="Denver",
        state="CO",
        postal_code="80205",
        latitude=39.7570,
        longitude=-104.9700,
        phone="+1-303-555-0143",
        website="http://ironcladstrength.example.com",
        primary_category="Gym",
        extra_categories=("Personal trainer",),
        description=(
            "Ironclad Strength is a barbell gym in Denver with platforms, competition "
            "bars and a coaching staff who actually programme for you. Membership covers "
            "open gym, the beginner barbell class and monthly form checks. We run "
            "powerlifting meets twice a year and keep the place open from five in the "
            "morning so shift workers can train before work."
        ),
        services=("Open gym membership", "Personal training", "Barbell classes",
                  "Powerlifting coaching"),
        search_terms=(
            "gym denver",
            "powerlifting gym denver",
            "24 hour gym near me",
            "personal trainer denver",
            "barbell gym five points",
            "weightlifting gym denver",
            "gym with platforms denver",
        ),
        booking_services=("Personal training", "Barbell classes", "Gym tour"),
        rivals=("Mile High Barbell", "Front Range Fitness", "Platform Athletic Club"),
        complaints=(
            "Half the platforms were roped off for a month with no notice and no refund.",
            "Cancelled my membership in person and they kept billing me for three months.",
            "Changing rooms smell and two of the showers have been broken since spring.",
            "Signed up for coaching and got a spreadsheet nobody ever looked at again.",
            "Front desk is unstaffed most evenings so you cannot get anything sorted.",
            "Air conditioning gave out in July and they just put a fan in the corner.",
        ),
        mixed=(
            "Good equipment, poor housekeeping. Bring your own wipes.",
            "Coaching is solid if you get the right coach. Ask around first.",
            "Busy between five and seven, you will wait for a rack.",
        ),
        praise=(
            "Best barbell setup in the city and the meet they ran was properly organised.",
            "Coach walked me through my first squat session and I have not looked back.",
            "Open at five in the morning, which no other gym here manages.",
            "Real platforms, calibrated plates and nobody filming themselves.",
        ),
        posts=(
            "Beginner barbell class starts again on the first Monday of the month.",
            "Winter meet registration is open for lifters at every level.",
            "New competition bars are on the back platforms this week.",
        ),
        attributes=(
            ("has_showers", "amenities"),
            ("locker_rooms", "amenities"),
            ("personal_training", "services"),
            ("group_classes", "services"),
            ("member_parking", "accessibility"),
        ),
        headline_problem="Invisible on every local search, including its own name",
        expected_grade="poor",
        failing=("visibility", "profile"),
        problems=Problems(
            # Visibility has collapsed: the pack is gone, three keywords never find the
            # profile at all, and a search for the gym's own name returns nothing.
            keyword_plan=(
                ("ironclad strength gym", "general", "gone"),
                ("gym denver", "general", "gone"),
                ("powerlifting gym denver", "general", "slip"),
                ("24 hour gym near me", "general", "gone"),
                ("personal trainer denver", "general", "gone"),
                ("barbell gym five points", "general", "near"),
                ("weightlifting gym denver", "general", "lost"),
                ("gym with platforms denver", "general", "mid"),
                ("strength gym denver", "general", "near"),
            ),
            losing_terms=3,
            rival_strength=2.6,
            # Profile: stuffed name, insecure link, no pin, barely any attributes answered.
            name_stuffed=True,
            phone=False,
            website="http",
            pin=False,
            verified=False,
            address_complete=False,
            additional_categories=1,
            opening_date=False,
            description="missing",
            logo=False,
            cover=False,
            attribute_share=0.22,
            accessibility_answered=False,
            open_days=("WEDNESDAY", "THURSDAY"),
            odd_hours=True,
            recent_mix=(8, 6, 4, 5, 6),
            prior_mix=(2, 2, 4, 8, 12),
            recent_last_30=2,
            reply_share=0.22,
            critical_reply_share=0.12,
            reply_delay_days=16,
            competitor_reviews=230,
            photos=3,
            photo_types=(0, 0, 0),
            videos=0,
            photo_age_days=196,
            posts_90d=2,
            last_post_days=52,
            post_types=("standard",),
            post_cta_share=0.2,
            bookings=BookingMix(new_stale=15, expired=9, confirmed=2, completed=8, cancelled=7,
                                no_show=5),
            weekend_requests=8,
            dominant_channel_share=0.97,
            unlisted_services=("Nutrition consult",),
            google_bookings_zero=True,
            lead_collapse=True,
            impressions_base=180,
            impressions_drop=0.40,
            calls_drop=0.52,
            directions_drop=0.46,
            clicks_drop=0.50,
            mobile_shift=0.12,
            zero_action_streak=3,
            missing_days=3,
        ),
    ),
    Archetype(
        key="maison-noir-salon",
        name="Maison Noir Hair Studio",
        industry="Hair salon",
        city="Portland",
        state="OR",
        postal_code="97214",
        latitude=45.5150,
        longitude=-122.6400,
        phone="+1-503-555-0119",
        website="https://maisonnoirhair.example.com",
        primary_category="Hair salon",
        extra_categories=("Beauty salon", "Hair extensions service"),
        description=(
            "Maison Noir is a small colour-focused hair studio in Portland. Three chairs, "
            "one colourist, and a waiting list that we keep honest. We specialise in "
            "lived-in blonde, corrective colour and curly cutting, and we book longer "
            "appointments than most salons so nothing is rushed. Consultations are free "
            "and every colour service includes a bond treatment."
        ),
        services=("Colour correction", "Balayage", "Curly cutting", "Bond treatment"),
        search_terms=(
            "hair salon portland",
            "balayage portland",
            "colour correction portland",
            "curly hair specialist portland",
            "hair extensions portland",
            "maison noir hair",
        ),
        booking_services=("Balayage", "Colour correction", "Curly cutting"),
        rivals=("Alder & Ash Salon", "Studio Verde", "Rosewater Hair Co"),
        complaints=(
            "Booked a correction, left with two different colours and a burnt hairline.",
            "Turned up for my appointment and the stylist had gone home sick with no call.",
            "Quoted one price at consultation and charged nearly double at the till.",
            "Cut was uneven on one side and they would not book me in to fix it.",
            "Nobody answers the phone and the booking form has been broken for weeks.",
            "Was left with bleach on far too long and my scalp blistered.",
        ),
        mixed=(
            "Colour was lovely, the wait to get in is nearly three months.",
            "Talented stylist, chaotic front desk.",
            "Good work but they run behind by an hour most days.",
        ),
        praise=(
            "Best balayage I have had in this city and she actually listened to me.",
            "Fixed a box-dye disaster in one sitting without frying my hair.",
            "Curly cut was dry-cut properly and my hair has never sat better.",
            "Free consultation was honest about what my hair could take.",
        ),
        posts=(
            "Autumn colour slots are open for lived-in blonde and root melts.",
            "Free curly consultations run every other Tuesday afternoon.",
            "Bond treatment is included with every colour service this season.",
        ),
        attributes=(
            ("appointment_only", "planning"),
            ("hair_colouring", "services"),
            ("hair_extensions", "services"),
            ("curly_hair_specialist", "services"),
            ("gender_neutral_pricing", "services"),
        ),
        headline_problem="Three photos, nothing ever posted, open two weekdays on paper",
        expected_grade="fair",
        failing=("content", "reputation", "performance"),
        problems=Problems(
            # Content is the disaster: three photos, none categorised, nothing ever posted.
            photos=3,
            photo_types=(0, 0, 0),
            videos=0,
            photo_age_days=291,
            posts_90d=0,
            last_post_days=0,
            post_types=(),
            post_cta_share=0.0,
            logo=False,
            cover=False,
            # Profile: half a week of hours, a two-line description, no opening date.
            open_days=("THURSDAY", "FRIDAY"),
            odd_hours=True,
            description="short",
            opening_date=False,
            additional_categories=1,
            pin=False,
            address_complete=False,
            attribute_share=0.25,
            accessibility_answered=False,
            recent_mix=(7, 5, 4, 5, 9),
            prior_mix=(3, 2, 3, 7, 14),
            recent_last_30=2,
            reply_share=0.24,
            critical_reply_share=0.14,
            reply_delay_days=17,
            competitor_reviews=180,
            verified=False,
            keyword_plan=(
                ("maison noir hair", "general", "gone"),
                ("hair salon portland", "general", "slip"),
                ("balayage portland", "cosmetic", "near"),
                ("colour correction portland", "cosmetic", "lost"),
                ("curly hair specialist portland", "general", "gone"),
                ("hair extensions portland", "general", "gone"),
                ("hair colourist portland", "cosmetic", "gone"),
                ("blonde specialist portland", "cosmetic", "near"),
                ("hair studio portland", "general", "mid"),
            ),
            losing_terms=2,
            rival_strength=2.2,
            bookings=BookingMix(new_stale=10, expired=6, confirmed=4, completed=11, cancelled=7,
                                no_show=4),
            weekend_requests=8,
            dominant_channel_share=0.97,
            unlisted_services=("Bridal party styling",),
            google_bookings_zero=True,
            impressions_base=150,
            impressions_drop=0.34,
            calls_drop=0.52,
            directions_drop=0.46,
            clicks_drop=0.50,
            zero_action_streak=3,
            missing_days=3,
        ),
    ),
    Archetype(
        key="carter-auto-works",
        name="Carter Auto Works",
        industry="Auto repair",
        city="Phoenix",
        state="AZ",
        postal_code="85004",
        latitude=33.4520,
        longitude=-112.0700,
        phone="+1-602-555-0176",
        website="https://carterautoworks.example.com",
        primary_category="Auto repair shop",
        extra_categories=("Brake shop", "Oil change service", "Tire shop"),
        description=(
            "Carter Auto Works has been fixing cars in central Phoenix since 1998. We "
            "handle brakes, suspension, air conditioning, diagnostics and state "
            "inspections for most makes, and we will tell you when a repair is not worth "
            "the money. Two lifts, four technicians, and a waiting room with decent "
            "coffee. Loaner cars are available for jobs that run past a day."
        ),
        services=("Brake service", "Oil change", "Tire rotation", "Air conditioning repair"),
        search_terms=(
            "auto repair phoenix",
            "brake repair near me",
            "oil change phoenix",
            "car ac repair phoenix",
            "mechanic central phoenix",
            "emergency car repair phoenix",
            "tire shop phoenix",
        ),
        booking_services=("Brake service", "Oil change", "Air conditioning repair"),
        rivals=("Desert Ridge Automotive", "Copper State Motors", "Grand Avenue Garage"),
        complaints=(
            "Left three voicemails about a booking and never heard back from anyone.",
            "Car sat on the lot for four days before anyone looked at it.",
            "Quoted four hundred, invoiced nine hundred, and the noise came back in a week.",
            "Booked online for Saturday and turned up to a locked gate.",
            "They replaced a part that was not broken and could not explain why.",
            "Was told the loaner was ready and then told there had never been one.",
        ),
        mixed=(
            "Work is usually right, the front office is a mess.",
            "Fair prices when they actually get to your car.",
            "Good diagnostics, terrible at calling you back.",
        ),
        praise=(
            "Talked me out of a repair I did not need, which is rare and appreciated.",
            "Fixed an air conditioning fault two other shops missed.",
            "Honest quote, done the same day, no surprises on the invoice.",
            "Been taking my truck here for a decade and they have never let me down.",
        ),
        posts=(
            "Summer air conditioning checks are running through August.",
            "State inspections are done while you wait most weekday mornings.",
            "Brake and rotor packages are available on most common models.",
        ),
        attributes=(
            ("oil_change", "services"),
            ("brake_service", "services"),
            ("loaner_vehicles", "services"),
            ("waiting_area", "amenities"),
            ("courtesy_shuttle", "services"),
        ),
        headline_problem="18 booking requests never answered and a third of visits lost",
        expected_grade="fair",
        failing=("operations", "reputation"),
        problems=Problems(
            # Operations is the disaster: nobody works the booking queue.
            bookings=BookingMix(new_stale=18, expired=11, confirmed=2, completed=8, cancelled=8,
                                no_show=5),
            weekend_requests=10,
            dominant_channel_share=0.97,
            unlisted_services=("Windshield replacement", "Transmission flush"),
            google_bookings_zero=True,
            lead_collapse=True,
            open_days=("MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"),
            # Reputation follows from it: complaints about silence, nobody replying.
            recent_mix=(13, 8, 5, 4, 4),
            prior_mix=(5, 4, 5, 8, 12),
            recent_last_30=2,
            reply_share=0.18,
            critical_reply_share=0.10,
            reply_delay_days=18,
            competitor_reviews=260,
            description="thin",
            verified=False,
            additional_categories=1,
            opening_date=False,
            pin=False,
            logo=False,
            cover=False,
            attribute_share=0.35,
            accessibility_answered=False,
            keyword_plan=(
                ("carter auto works phoenix", "general", "mid"),
                ("auto repair phoenix", "general", "slip"),
                ("brake repair near me", "general", "near"),
                ("oil change phoenix", "general", "mid"),
                ("emergency car repair phoenix", "emergency", "gone"),
                ("mechanic central phoenix", "general", "lost"),
                ("tire shop phoenix", "general", "gone"),
            ),
            losing_terms=2,
            rival_strength=2.0,
            photos=8,
            photo_types=(5, 0, 0),
            videos=0,
            photo_age_days=118,
            posts_90d=2,
            last_post_days=62,
            post_types=("standard",),
            post_cta_share=0.3,
            impressions_base=200,
            impressions_drop=0.24,
            calls_drop=0.36,
            directions_drop=0.30,
            clicks_drop=0.33,
            zero_action_streak=3,
            missing_days=3,
        ),
    ),
    Archetype(
        key="brightsmile-family-dental",
        name="Brightsmile Family Dental",
        industry="Dental",
        city="Tampa",
        state="FL",
        postal_code="33606",
        latitude=27.9400,
        longitude=-82.4800,
        phone="+1-813-555-0155",
        website="http://brightsmilefamilydental.example.com",
        primary_category="Dental clinic",
        extra_categories=("Pediatric dentist", "Orthodontist"),
        description=(
            "Brightsmile Family Dental looks after families across south Tampa. Cleanings, "
            "fillings, crowns, clear aligners and children's dentistry from age two, with "
            "digital scanning so nobody has to bite on putty. Most PPO plans are accepted "
            "and we offer interest-free payment plans on longer treatment. Evening "
            "appointments run on Wednesdays and the practice is fully wheelchair "
            "accessible."
        ),
        services=("Teeth whitening", "Clear aligners", "Children's dentistry",
                  "Emergency appointments"),
        search_terms=(
            "dentist tampa",
            "family dentist south tampa",
            "kids dentist tampa",
            "emergency dentist tampa",
            "clear aligners tampa",
            "dental cleaning tampa",
        ),
        booking_services=("Dental cleaning", "Clear aligners", "Children's dentistry"),
        rivals=("Bayshore Dental Group", "Hyde Park Smiles", "Gulfview Family Dentistry"),
        complaints=(
            "Waited an hour past my appointment time twice in a row with no apology.",
            "Was billed for a procedure my insurance had already covered and nobody would "
            "look into it.",
            "Hygienist was rough and my gums bled for two days afterwards.",
            "Called about a broken crown on a Friday and never got a call back.",
            "Treatment plan kept growing every visit without anyone explaining why.",
            "The children's room was closed and my son had to sit in the main waiting area "
            "for forty minutes.",
        ),
        mixed=(
            "Dentist is good, the front desk loses paperwork constantly.",
            "Fine for a cleaning, would not go back for anything complicated.",
            "Clean practice, long waits, mixed billing experience.",
        ),
        praise=(
            "Dr. Okafor is patient with nervous patients and explains every step.",
            "Got my son through his first filling without a single tear.",
            "Aligner treatment finished ahead of schedule and the result is great.",
            "Same-day appointment for a cracked tooth, sorted in under an hour.",
        ),
        posts=(
            "Back-to-school checkups are open for children from age two.",
            "Clear aligner consultations include a free digital scan this month.",
            "Evening appointments run every Wednesday until eight.",
        ),
        attributes=(
            ("accepts_insurance", "payments"),
            ("payment_plans_available", "payments"),
            ("pediatric_care", "services"),
            ("orthodontic_care", "services"),
            ("teeth_whitening", "services"),
            ("emergency_services", "services"),
            ("sedation_available", "services"),
            ("digital_xray", "services"),
        ),
        headline_problem="Unverified listing, contradictory services, complaints unanswered",
        expected_grade="fair",
        failing=("profile", "reputation"),
        problems=Problems(
            # Profile is the disaster: unverified, contradictory, half-answered.
            verified=False,
            website="http",
            address_complete=False,
            pin=False,
            description="short",
            opening_date=False,
            logo=False,
            cover=False,
            additional_categories=2,  # both kept, so the category/attribute contradiction shows
            attribute_share=0.22,
            accessibility_answered=False,
            attributes_denied=("pediatric_care",),
            open_days=("MONDAY", "WEDNESDAY"),
            odd_hours=True,
            # Reputation: enough complaints, few replies.
            recent_mix=(9, 7, 5, 5, 6),
            prior_mix=(3, 3, 4, 9, 15),
            recent_last_30=3,
            reply_share=0.28,
            critical_reply_share=0.15,
            reply_delay_days=14,
            competitor_reviews=240,
            keyword_plan=(
                ("brightsmile dental tampa", "general", "gone"),
                ("dentist tampa", "general", "slip"),
                ("family dentist south tampa", "general", "near"),
                ("kids dentist tampa", "pediatric", "lost"),
                ("emergency dentist tampa", "emergency", "gone"),
                ("clear aligners tampa", "orthodontics", "mid"),
                ("dental cleaning tampa", "general", "gone"),
            ),
            losing_terms=2,
            rival_strength=2.4,
            bookings=BookingMix(new_stale=9, expired=5, confirmed=5, completed=12, cancelled=7,
                                no_show=4),
            weekend_requests=8,
            dominant_channel_share=0.90,
            photos=9,
            photo_types=(6, 0, 0),
            videos=0,
            photo_age_days=104,
            posts_90d=2,
            last_post_days=56,
            post_types=("standard", "offer"),
            post_cta_share=0.35,
            impressions_base=190,
            impressions_drop=0.31,
            calls_drop=0.45,
            directions_drop=0.38,
            clicks_drop=0.42,
            missing_days=3,
        ),
    ),
    Archetype(
        key="paws-and-claws-vet",
        name="Paws & Claws Veterinary Clinic",
        industry="Veterinary",
        city="Nashville",
        state="TN",
        postal_code="37206",
        latitude=36.1800,
        longitude=-86.7400,
        phone="+1-615-555-0132",
        website="https://pawsandclawsvet.example.com",
        primary_category="Veterinarian",
        extra_categories=("Animal hospital", "Emergency veterinarian service"),
        description=(
            "Paws & Claws is a small-animal clinic in east Nashville with two vets and an "
            "in-house laboratory, so most bloodwork comes back the same visit. We handle "
            "wellness plans, dentistry, soft-tissue surgery and after-hours emergencies "
            "for dogs, cats and rabbits. Fear-free handling is standard, and we keep "
            "separate waiting areas so cats are not sat next to dogs."
        ),
        services=("Wellness exams", "Dental cleaning", "Soft tissue surgery",
                  "Emergency visits"),
        search_terms=(
            "vet nashville",
            "emergency vet near me",
            "cat vet east nashville",
            "dog dental cleaning nashville",
            "animal hospital nashville",
            "rabbit vet nashville",
        ),
        booking_services=("Wellness exams", "Dental cleaning", "Emergency visits"),
        rivals=("Cumberland Animal Hospital", "East Bank Veterinary", "Music City Pet Care"),
        complaints=(
            "Phones ring out all afternoon and the online form never gets answered.",
            "Was quoted for a dental and charged for three extractions nobody mentioned.",
            "Waited two hours with a bleeding dog because there was only one vet on.",
            "They lost my cat's vaccination history and blamed the previous practice.",
            "Emergency line went to voicemail on a Sunday when the site says it is staffed.",
            "Discharge notes were wrong and the medication dose did not match the label.",
        ),
        mixed=(
            "Vets are kind, the admin side is unreliable.",
            "Good care when you can get in, which is the problem.",
            "Prices crept up sharply this year without any notice.",
        ),
        praise=(
            "They fitted my rabbit in the same morning and handled her beautifully.",
            "Fear-free handling is real here, my anxious dog walks in happily now.",
            "In-house bloods meant we had answers within the hour.",
            "Separate cat waiting room makes a genuine difference.",
        ),
        posts=(
            "Wellness plans for puppies and kittens cover vaccinations and two check-ups.",
            "Dental month runs through February with free pre-assessment.",
            "Our after-hours emergency line is staffed until eleven on weeknights.",
        ),
        attributes=(
            ("emergency_services", "services"),
            ("in_house_laboratory", "services"),
            ("surgery_available", "services"),
            ("exotic_pets", "services"),
            ("cat_only_waiting_area", "amenities"),
        ),
        headline_problem="Impressions down by half, with four days nobody called or clicked",
        expected_grade="fair",
        failing=("performance", "operations"),
        problems=Problems(
            # Performance has fallen off a cliff and the export has holes in it.
            impressions_base=420,
            impressions_drop=0.42,
            calls_drop=0.56,
            directions_drop=0.52,
            clicks_drop=0.58,
            maps_shift=0.14,
            mobile_shift=0.12,
            zero_action_streak=4,
            missing_days=4,
            # Operations: nobody answers, and half the visits never happen.
            bookings=BookingMix(new_stale=12, expired=7, confirmed=4, completed=10, cancelled=8,
                                no_show=5),
            weekend_requests=9,
            dominant_channel_share=0.93,
            unlisted_services=("Boarding overnight",),
            google_bookings_zero=True,
            lead_collapse=True,
            recent_mix=(6, 5, 5, 7, 10),
            prior_mix=(2, 3, 4, 9, 16),
            recent_last_30=4,
            reply_share=0.40,
            critical_reply_share=0.30,
            reply_delay_days=12,
            competitor_reviews=200,
            description="thin",
            opening_date=False,
            pin=False,
            logo=False,
            cover=False,
            additional_categories=1,
            attribute_share=0.40,
            accessibility_answered=False,
            keyword_plan=(
                ("paws and claws vet", "general", "mid"),
                ("vet nashville", "general", "slip"),
                ("emergency vet near me", "emergency", "gone"),
                ("cat vet east nashville", "general", "near"),
                ("dog dental cleaning nashville", "general", "lost"),
                ("animal hospital nashville", "general", "gone"),
                ("rabbit vet nashville", "general", "mid"),
            ),
            losing_terms=2,
            rival_strength=1.9,
            photos=11,
            photo_types=(8, 0, 0),
            videos=0,
            photo_age_days=96,
            posts_90d=3,
            last_post_days=42,
            post_types=("standard",),
            post_cta_share=0.35,
        ),
    ),
    Archetype(
        key="bluebird-coffee",
        name="Bluebird Coffee House",
        industry="Coffee shop",
        city="Seattle",
        state="WA",
        postal_code="98122",
        latitude=47.6100,
        longitude=-122.3100,
        phone="+1-206-555-0164",
        website="https://bluebirdcoffeehouse.example.com",
        primary_category="Coffee shop",
        extra_categories=("Cafe", "Breakfast restaurant"),
        description=(
            "Bluebird Coffee House roasts in small batches two blocks from the shop and "
            "pours single-origin filter alongside the usual espresso. The kitchen does a "
            "short breakfast menu until noon and there is a back room with power sockets "
            "that we keep laptop-friendly on weekdays. Beans are available by the bag and "
            "we run a free cupping on the first Saturday of every month."
        ),
        services=("Espresso bar", "Filter coffee", "Breakfast menu", "Whole bean retail"),
        search_terms=(
            "coffee shop seattle",
            "best coffee capitol hill",
            "cafe with wifi seattle",
            "breakfast seattle",
            "specialty coffee seattle",
            "coffee roaster seattle",
        ),
        booking_services=("Cupping session", "Private hire", "Breakfast menu"),
        rivals=("Elliott Bay Roasters", "Pike Lane Coffee", "Union Street Espresso"),
        complaints=(
            "Ordered ahead and the drink was still not started fifteen minutes later.",
            "Back room has been full of stock boxes for weeks and there is nowhere to sit.",
            "Milk was scalded and the second attempt was no better.",
            "Card machine is down more often than it works and there is no sign about it.",
            "Staff were chatting behind the bar while six people waited.",
            "Pastries were clearly from the day before and nobody said so.",
        ),
        mixed=(
            "Coffee is good, the seating situation is hopeless after nine.",
            "Nice beans, slow service at the weekend.",
            "Great filter, the breakfast menu has shrunk a lot.",
        ),
        praise=(
            "The single-origin filter here is the best in the neighbourhood by a distance.",
            "Free cupping on Saturday was genuinely interesting and nobody was snobby.",
            "Barista remembered my order after two visits.",
            "Beans by the bag are roasted within the week, which you can taste.",
        ),
        posts=(
            "This month's single origin is a washed Ethiopian on the filter bar.",
            "Free cupping runs on the first Saturday, no booking needed.",
            "Breakfast is served until noon every day of the week.",
        ),
        attributes=(
            ("serves_breakfast", "services"),
            ("takeaway", "services"),
            ("outdoor_seating", "amenities"),
            ("good_for_working", "amenities"),
            ("vegan_options", "services"),
        ),
        headline_problem="Five photos, nothing posted since spring, slipping out of the map pack",
        expected_grade="fair",
        failing=("content", "reputation"),
        problems=Problems(
            # Content is the weak spot; everything else is merely tired.
            photos=5,
            photo_types=(0, 0, 0),
            videos=0,
            photo_age_days=148,
            posts_90d=0,
            last_post_days=104,
            post_types=("standard",),
            post_cta_share=0.0,
            opening_date=False,
            keyword_plan=(
                ("bluebird coffee house", "general", "mid"),
                ("coffee shop seattle", "general", "mid"),
                ("best coffee capitol hill", "general", "near"),
                ("cafe with wifi seattle", "general", "lost"),
                ("breakfast seattle", "general", "mid"),
                ("specialty coffee seattle", "general", "pack"),
                ("coffee roaster seattle", "general", "near"),
            ),
            losing_terms=1,
            rival_strength=1.8,
            description="thin",
            cover=False,
            additional_categories=1,
            attribute_share=0.40,
            accessibility_answered=False,
            recent_mix=(3, 3, 5, 9, 15),
            prior_mix=(1, 2, 4, 10, 19),
            recent_last_30=6,
            reply_share=0.55,
            critical_reply_share=0.45,
            reply_delay_days=9,
            competitor_reviews=150,
            bookings=BookingMix(new_stale=7, expired=3, confirmed=6, completed=14, cancelled=6,
                                no_show=4),
            weekend_requests=6,
            dominant_channel_share=0.96,
            unlisted_services=("Private hire",),
            google_bookings_zero=True,
            impressions_base=230,
            impressions_drop=0.18,
            calls_drop=0.27,
            directions_drop=0.22,
            clicks_drop=0.25,
        ),
    ),
    Archetype(
        key="greenleaf-pharmacy",
        name="Greenleaf Community Pharmacy",
        industry="Pharmacy",
        city="Columbus",
        state="OH",
        postal_code="43215",
        latitude=39.9600,
        longitude=-83.0000,
        phone="",
        website="",
        primary_category="Pharmacy",
        extra_categories=("Drug store",),
        description="",
        services=("Prescription filling", "Vaccinations", "Medication reviews",
                  "Compounding"),
        search_terms=(
            "pharmacy columbus",
            "pharmacy near me open now",
            "flu shot columbus",
            "compounding pharmacy columbus",
            "prescription delivery columbus",
        ),
        booking_services=("Vaccinations", "Medication reviews", "Prescription filling"),
        rivals=("Scioto Drug Co", "Franklin Family Pharmacy", "High Street Chemists"),
        complaints=(
            "The listed hours are wrong so I drove across town to a locked door.",
            "Prescription was not ready three days running and nobody called to explain.",
            "Cannot find a phone number anywhere, the listing has none.",
            "Staff were helpful but the wait was over an hour with one person on the counter.",
            "Flu clinic was cancelled and the only notice was a sign on the window.",
            "Was told my medication was out of stock after being told to come in for it.",
        ),
        mixed=(
            "Pharmacist is excellent, the systems around him are not.",
            "Good for compounding, unreliable for everything routine.",
            "Cheaper than the chains if you can get through on the phone.",
        ),
        praise=(
            "The pharmacist spent twenty minutes going through my mother's medication list.",
            "They compounded a liquid dose for my daughter when nobody else would.",
            "Delivery to the house every fortnight has been faultless.",
            "Actually knows my name, which the big chains never managed.",
        ),
        posts=(
            "Flu and shingles vaccinations are available without an appointment.",
            "Free medication reviews run on Tuesday and Thursday mornings.",
            "Prescription delivery covers the whole of downtown Columbus.",
        ),
        attributes=(
            ("vaccinations", "services"),
            ("compounding", "services"),
            ("prescription_delivery", "services"),
            ("drive_through", "services"),
            ("otc_medication", "services"),
        ),
        headline_problem="No phone, no website, no description, and an unverified listing",
        expected_grade="poor",
        failing=("profile", "content"),
        problems=Problems(
            # Profile is barely a listing at all.
            phone=False,
            website=None,
            address_complete=False,
            pin=False,
            verified=False,
            opening_date=False,
            description="missing",
            logo=False,
            cover=False,
            additional_categories=1,
            open_days=("WEDNESDAY", "THURSDAY"),
            attribute_share=0.15,
            accessibility_answered=False,
            # Content follows: three photos, nothing ever published.
            photos=3,
            photo_types=(0, 0, 0),
            videos=0,
            photo_age_days=334,
            posts_90d=0,
            last_post_days=0,  # zero posts stored at all
            post_types=(),
            post_cta_share=0.0,
            recent_mix=(8, 5, 5, 6, 9),
            prior_mix=(3, 3, 4, 8, 14),
            recent_last_30=2,
            reply_share=0.25,
            critical_reply_share=0.12,
            reply_delay_days=16,
            competitor_reviews=220,
            keyword_plan=(
                ("greenleaf pharmacy columbus", "general", "gone"),
                ("pharmacy columbus", "general", "slip"),
                ("pharmacy near me open now", "general", "near"),
                ("flu shot columbus", "general", "gone"),
                ("compounding pharmacy columbus", "general", "lost"),
                ("prescription delivery columbus", "general", "gone"),
                ("24 hour pharmacy columbus", "general", "gone"),
                ("medication review columbus", "general", "near"),
                ("chemist columbus ohio", "general", "mid"),
            ),
            losing_terms=2,
            rival_strength=2.1,
            bookings=BookingMix(new_stale=14, expired=8, confirmed=2, completed=8, cancelled=7,
                                no_show=5),
            weekend_requests=8,
            dominant_channel_share=0.97,
            unlisted_services=("Blister packing",),
            google_bookings_zero=True,
            lead_collapse=True,
            impressions_base=170,
            impressions_drop=0.41,
            calls_drop=0.55,
            directions_drop=0.50,
            clicks_drop=0.53,
            zero_action_streak=3,
            missing_days=3,
        ),
    ),
    Archetype(
        key="hartley-law",
        name="Hartley & Boyd Law Offices",
        industry="Law firm",
        city="Chicago",
        state="IL",
        postal_code="60604",
        latitude=41.8780,
        longitude=-87.6280,
        phone="+1-312-555-0197",
        website="https://hartleyboyd.example.com",
        primary_category="Law firm",
        extra_categories=("Personal injury attorney", "Family law attorney"),
        description=(
            "Hartley & Boyd is a six-attorney practice in the Loop handling personal "
            "injury, family law and landlord-tenant disputes across Cook County. First "
            "consultations are free and injury work is taken on contingency. We answer in "
            "English, Spanish and Polish, and we will tell you plainly when a claim is not "
            "worth bringing rather than billing you to find out."
        ),
        services=("Personal injury claims", "Family law", "Landlord tenant disputes",
                  "Free consultation"),
        search_terms=(
            "lawyer chicago",
            "personal injury attorney chicago",
            "family lawyer loop chicago",
            "free legal consultation chicago",
            "tenant lawyer chicago",
            "car accident lawyer chicago",
        ),
        booking_services=("Free consultation", "Family law", "Personal injury claims"),
        rivals=("Whitfield Injury Law", "Lakeshore Legal Partners", "Dearborn Advocates"),
        complaints=(
            "Three weeks without a single update and then a bill for reviewing my file.",
            "The attorney who took my case handed it to a paralegal I never met.",
            "Free consultation turned into a hard sell for a retainer I did not need.",
            "Missed a filing deadline and I found out from the court, not from them.",
            "Calls go to a shared voicemail box nobody appears to check.",
            "Was told the case was strong, then dropped a month before the hearing.",
        ),
        mixed=(
            "Won the case, communication throughout was poor.",
            "Competent lawyers, slow to respond to anything by email.",
            "Fair on fees, vague on timelines.",
        ),
        praise=(
            "Settled my injury claim for more than I expected and explained every step.",
            "Handled a difficult custody matter with real care.",
            "Told me honestly that I did not have a case, which saved me thousands.",
            "Polish-speaking attorney made the whole process possible for my parents.",
        ),
        posts=(
            "Free injury consultations are available in the Loop office every Thursday.",
            "New guidance on Cook County eviction timelines is on our site.",
            "We now handle family law matters in Spanish and Polish.",
        ),
        attributes=(
            ("free_consultation", "services"),
            ("contingency_fees", "payments"),
            ("language_assistance", "planning"),
            ("virtual_appointments", "planning"),
            ("evening_consultations", "planning"),
        ),
        headline_problem="Nowhere near the map pack, and 46 reviews against rivals' 420",
        expected_grade="fair",
        failing=("visibility", "reputation"),
        problems=Problems(
            keyword_plan=(
                ("hartley and boyd", "general", "mid"),
                ("lawyer chicago", "general", "gone"),
                ("personal injury attorney chicago", "general", "slip"),
                ("family lawyer loop chicago", "general", "near"),
                ("free legal consultation chicago", "general", "lost"),
                ("tenant lawyer chicago", "general", "drop"),
                ("car accident lawyer chicago", "emergency", "gone"),
            ),
            losing_terms=2,
            rival_strength=4.0,
            competitor_reviews=420,
            recent_mix=(4, 3, 3, 5, 8),
            prior_mix=(2, 2, 2, 6, 11),
            recent_last_30=2,
            reply_share=0.45,
            critical_reply_share=0.35,
            reply_delay_days=12,
            description="long",
            attribute_share=0.40,
            accessibility_answered=False,
            opening_date=False,
            pin=False,
            logo=False,
            cover=False,
            additional_categories=1,
            open_days=("MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"),
            photos=12,
            photo_types=(7, 0, 0),
            videos=0,
            photo_age_days=128,
            posts_90d=3,
            last_post_days=52,
            post_types=("standard",),
            post_cta_share=0.3,
            bookings=BookingMix(new_stale=5, expired=2, confirmed=8, completed=17, cancelled=6,
                                no_show=3),
            impressions_base=160,
            impressions_drop=0.23,
            calls_drop=0.33,
            directions_drop=0.27,
            clicks_drop=0.30,
            missing_days=3,
        ),
    ),
    Archetype(
        key="rapid-flow-plumbing",
        name="Rapid Flow Plumbing",
        industry="Plumber",
        city="Kansas City",
        state="MO",
        postal_code="64108",
        latitude=39.0850,
        longitude=-94.5800,
        phone="+1-816-555-0128",
        website="https://rapidflowplumbing.example.com",
        primary_category="Plumber",
        extra_categories=("Drainage service", "Water heater supplier"),
        description=(
            "Rapid Flow Plumbing covers Kansas City and the surrounding suburbs for "
            "drains, water heaters, burst pipes and bathroom fit-outs. Two vans are on "
            "call for out-of-hours work and we quote before we start, not after. Our "
            "technicians are licensed in Missouri and Kansas, and every job comes with a "
            "twelve-month workmanship guarantee."
        ),
        services=("Drain clearing", "Water heater replacement", "Burst pipe repair",
                  "Bathroom installation"),
        search_terms=(
            "plumber kansas city",
            "emergency plumber near me",
            "drain cleaning kansas city",
            "water heater repair kansas city",
            "burst pipe kansas city",
            "bathroom plumber kansas city",
        ),
        booking_services=("Drain clearing", "Water heater replacement", "Burst pipe repair"),
        rivals=("Midtown Mechanical", "Kaw Valley Plumbing", "Westport Drain Co"),
        complaints=(
            "Booked an emergency call at eight and nobody arrived or phoned until the "
            "next afternoon.",
            "Quoted over the phone, charged nearly double on the day for the same job.",
            "The new water heater leaked within a fortnight and the guarantee was a "
            "runaround.",
            "Technician left the bathroom floor soaked and the old parts in the garden.",
            "Three separate appointments cancelled at short notice by text.",
            "Nobody answers the out-of-hours number that the listing advertises.",
        ),
        mixed=(
            "Work was fine, the scheduling is a lottery.",
            "Good on drains, expensive on everything else.",
            "Turned up eventually and did a tidy job.",
        ),
        praise=(
            "Cleared a blocked main on a Sunday within two hours of calling.",
            "Replaced the heater same day and took the old one away.",
            "Quoted honestly and stuck to it, which is rarer than it should be.",
            "Left the bathroom cleaner than they found it.",
        ),
        posts=(
            "Winter pipe checks are booking now before the first freeze.",
            "Water heater replacements include removal of the old unit.",
            "Our out-of-hours van covers the metro area seven days a week.",
        ),
        attributes=(
            ("emergency_services", "services"),
            ("licensed_technicians", "services"),
            ("free_estimates", "services"),
            ("service_area_business", "planning"),
            ("warranty_offered", "services"),
        ),
        headline_problem="Emergency calls unanswered, a third of visits missed, calls down half",
        expected_grade="fair",
        failing=("operations", "performance"),
        problems=Problems(
            bookings=BookingMix(new_stale=13, expired=8, confirmed=3, completed=9, cancelled=8,
                                no_show=5),
            weekend_requests=9,
            dominant_channel_share=0.92,
            unlisted_services=("Septic tank pumping",),
            google_bookings_zero=True,
            lead_collapse=True,
            open_days=("MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"),
            impressions_base=210,
            impressions_drop=0.30,
            calls_drop=0.40,
            directions_drop=0.34,
            clicks_drop=0.38,
            mobile_shift=0.11,
            zero_action_streak=3,
            missing_days=3,
            recent_mix=(6, 5, 4, 7, 10),
            prior_mix=(3, 3, 4, 8, 14),
            recent_last_30=5,
            reply_share=0.50,
            critical_reply_share=0.42,
            reply_delay_days=10,
            competitor_reviews=180,
            description="thin",
            attribute_share=0.40,
            accessibility_answered=False,
            opening_date=False,
            pin=False,
            logo=False,
            address_complete=False,
            additional_categories=1,
            keyword_plan=(
                ("rapid flow plumbing", "general", "mid"),
                ("plumber kansas city", "general", "slip"),
                ("emergency plumber near me", "emergency", "lost"),
                ("drain cleaning kansas city", "general", "near"),
                ("water heater repair kansas city", "general", "mid"),
                ("burst pipe kansas city", "emergency", "gone"),
                ("bathroom plumber kansas city", "general", "mid"),
            ),
            losing_terms=1,
            rival_strength=1.7,
            photos=14,
            photo_types=(9, 0, 0),
            videos=0,
            photo_age_days=94,
            posts_90d=3,
            last_post_days=38,
            post_types=("standard", "offer"),
            post_cta_share=0.45,
        ),
    ),
)

KEYS: tuple[str, ...] = tuple(a.key for a in ARCHETYPES)
BY_KEY: dict[str, Archetype] = {a.key: a for a in ARCHETYPES}


def by_key(key: str) -> Archetype:
    try:
        return BY_KEY[key]
    except KeyError:
        raise KeyError(f"Unknown demo profile key: {key}") from None


assert len(KEYS) == len(set(KEYS)) == 10, "ten archetypes, each with a unique key"
assert len({a.industry for a in ARCHETYPES}) == 10, "ten distinct industries"
assert len({a.primary_category for a in ARCHETYPES}) == 10, "ten distinct Google categories"
