# Data Schema Reference

## mock_destinations.json

Array of destination objects.

```json
[
  {
    "id": "bali_indonesia",
    "name": "Bali",
    "country": "Indonesia",
    "continent": "Asia",
    "region": "Southeast Asia",
    "city_type": "island",
    "estimated_daily_cost_usd": {
      "budget": 35,
      "moderate": 75,
      "comfortable": 140,
      "luxury": 300
    },
    "travel_styles": ["beach", "relaxation", "cultural", "adventure", "nature", "foodie"],
    "best_seasons": ["spring", "summer"],
    "okay_seasons": ["autumn"],
    "avoid_seasons": ["winter"],
    "avg_temp_c": {
      "spring": 28, "summer": 29, "autumn": 28, "winter": 27
    },
    "weather_notes": "Dry season Apr-Sep, wet season Oct-Mar",
    "visa_on_arrival": ["USA", "UK", "EU", "AUS"],
    "visa_required": [],
    "language": "Balinese/Indonesian",
    "currency": "IDR",
    "typical_stay_days": 10,
    "direct_flights_from": ["Singapore", "Sydney", "Tokyo", "Dubai", "Hong Kong"],
    "airport_code": "DPS",
    "highlights": [
      "Tegallalang Rice Terraces",
      "Tanah Lot Temple",
      "Ubud Monkey Forest",
      "Seminyak Beach",
      "Uluwatu Cliff Temple",
      "Kuta Beach"
    ],
    "known_for": ["Surfing", "Yoga retreats", "Temples", "Rice terraces", "Nightlife", "Spa"],
    "description": "Tropical paradise with ancient temples, lush rice terraces, and world-class surf breaks",
    "insider_tip": "Stay in Ubud for culture, Canggu for surf/nightlife, Nusa Dua for luxury",
    "places": [
      {
        "name": "Tegallalang Rice Terraces",
        "type": "nature",
        "open_time": "06:00",
        "close_time": "18:00",
        "best_visit_time": "07:00-09:00",
        "crowd_peak": "10:00-14:00",
        "duration_hours": 2,
        "entrance_fee_usd": 2,
        "lat": -8.43,
        "lon": 115.28,
        "neighborhood": "Ubud",
        "notes": "Visit at sunrise for best light and fewer crowds"
      }
    ]
  }
]
```

---

## mock_flights.json

Routes keyed by `ORIGIN->DEST` (uppercase city names).

```json
{
  "routes": {
    "NEW YORK->BALI": [
      {
        "airline": "Singapore Airlines",
        "flight_number": "SQ22",
        "price_usd_economy": 820,
        "price_usd_business": 2400,
        "duration_hours": 21.5,
        "stops": 1,
        "stop_cities": ["Singapore"],
        "departure_times": ["08:00", "14:30", "22:00"],
        "baggage_kg": 30,
        "rating": 4.7
      },
      {
        "airline": "Cathay Pacific",
        "flight_number": "CX831",
        "price_usd_economy": 760,
        "price_usd_business": 2100,
        "duration_hours": 23,
        "stops": 1,
        "stop_cities": ["Hong Kong"],
        "departure_times": ["11:00", "23:45"],
        "baggage_kg": 25,
        "rating": 4.5
      }
    ]
  },
  "price_multipliers": {
    "summer": 1.3,
    "winter": 0.8,
    "spring": 1.0,
    "autumn": 0.9
  },
  "group_discount": {
    "5+": 0.05,
    "10+": 0.10
  }
}
```

---

## mock_hotels.json

Hotels keyed by city name.

```json
{
  "Bali": [
    {
      "name": "Alaya Resort Ubud",
      "type": "resort",
      "stars": 5,
      "neighborhood": "Ubud",
      "price_per_night_usd": 180,
      "amenities": ["pool", "spa", "restaurant", "wifi", "breakfast_included", "airport_shuttle"],
      "distance_to_center_km": 0.5,
      "guest_rating": 9.2,
      "description": "Luxury jungle resort with infinity pool overlooking rice fields",
      "min_nights": 2
    },
    {
      "name": "The Layar Private Villas",
      "type": "villa",
      "stars": 5,
      "neighborhood": "Seminyak",
      "price_per_night_usd": 350,
      "amenities": ["private_pool", "butler", "breakfast_included", "beach_access"],
      "distance_to_center_km": 1.2,
      "guest_rating": 9.5,
      "description": "Private villas with personal butler and plunge pool",
      "min_nights": 3
    },
    {
      "name": "Canggu Surf Hostel",
      "type": "hostel",
      "stars": 0,
      "neighborhood": "Canggu",
      "price_per_night_usd": 18,
      "amenities": ["pool", "wifi", "surfboard_rental", "cafe"],
      "distance_to_center_km": 2.0,
      "guest_rating": 8.1,
      "description": "Social hostel in surf central with daily yoga classes",
      "min_nights": 1
    }
  ]
}
```

---

## mock_food.json

Food options keyed by city.

```json
{
  "Bali": {
    "street_food": [
      {
        "name": "Warung Babi Guling Ibu Oka",
        "type": "warung",
        "cuisine": "Balinese",
        "specialty": "Suckling pig (babi guling)",
        "avg_cost_per_person_usd": 4,
        "location": "Ubud Center",
        "open": "11:00",
        "close": "15:00",
        "reservation": false,
        "rating": 4.6,
        "vegetarian_options": false,
        "must_try": ["Babi guling rice plate", "Sate lilit"]
      }
    ],
    "budget": [...],
    "mid_range": [...],
    "fine_dining": [
      {
        "name": "Locavore",
        "type": "restaurant",
        "cuisine": "Modern Indonesian",
        "specialty": "Farm-to-table tasting menu",
        "avg_cost_per_person_usd": 85,
        "location": "Ubud",
        "open": "12:00",
        "close": "22:00",
        "reservation": true,
        "reservation_notes": "Book 2+ weeks in advance",
        "rating": 4.9,
        "vegetarian_options": true,
        "must_try": ["Chef's tasting menu", "Local ingredient cocktails"]
      }
    ],
    "food_notes": "Try nasi campur (mixed rice) for an authentic local meal under $3"
  }
}
```

---

## mock_transport.json

Transport options keyed by city.

```json
{
  "Bali": {
    "modes": {
      "taxi": {
        "available": true,
        "app": "Grab / Gojek",
        "base_fare_usd": 1.5,
        "per_km_usd": 0.4,
        "avg_city_ride_usd": 3,
        "notes": "Always use app-based taxis, avoid unmarked cabs"
      },
      "scooter_rental": {
        "available": true,
        "daily_rate_usd": 6,
        "weekly_rate_usd": 35,
        "deposit_usd": 20,
        "license_required": true,
        "license_type": "International Driver's License",
        "helmet_included": true,
        "fuel_per_day_usd": 2,
        "notes": "Most popular way to get around; be cautious on mountain roads"
      },
      "bicycle_rental": {
        "available": true,
        "daily_rate_usd": 5,
        "weekly_rate_usd": 28,
        "deposit_usd": 10,
        "electric_available": true,
        "electric_daily_rate_usd": 12
      },
      "private_driver": {
        "available": true,
        "half_day_usd": 35,
        "full_day_usd": 55,
        "notes": "Best for day trips to temples; driver waits while you visit"
      },
      "public_bus": {
        "available": true,
        "flat_fare_usd": 0.5,
        "notes": "Perama tourist shuttle connects main areas, $5-10 per route"
      }
    },
    "inter_city_transport": {
      "airport_to_seminyak": {
        "taxi_usd": 12,
        "grab_usd": 8,
        "shuttle_usd": 5,
        "duration_min": 30
      }
    },
    "transit_times_min": {
      "Ubud->Seminyak": 60,
      "Ubud->Canggu": 75,
      "Seminyak->Uluwatu": 45,
      "Airport->Ubud": 90
    }
  }
}
```
