import requests

API_KEY = "67fe2ee97bf388ca0cf76d8f"
API_ENDPOINT = "https://api.makcorps.com/city"

def get_hotel_pricing(location: str, group_size: int) -> str:
    """
    Fetch hotel pricing details based on location and group size.
    """
    params = {
        "location": location,
        "group_size": group_size,
        "api_key": API_KEY
    }
    response = requests.get(API_ENDPOINT, params=params)

    if response.status_code == 200:
        hotels = response.json()
        if hotels:
            hotel_info = []
            for hotel in hotels['data']:
                hotel_info.append(f"Hotel: {hotel['name']} - Price: ${hotel['price']} per night")
            return "\n".join(hotel_info)
        else:
            return "No hotels found for your destination."
    else:
        return "Error fetching hotel data. Please try again later."

def book_hotel(location: str, group_size: int) -> str:
    """
    Simulate hotel booking.
    """
    hotel_pricing = get_hotel_pricing(location, group_size)
    if "Error" in hotel_pricing:
        return hotel_pricing
    else:
        # Simulate the booking process
        return f"🏨 Hotel successfully booked in {location} for {group_size} people! {hotel_pricing}"
