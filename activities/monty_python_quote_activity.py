"""Activity for generating random Monty Python quotes."""
import random
from temporalio import activity
from dataclasses import dataclass
from typing import List


@dataclass
class QuoteResult:
    """Result from getting a random quote."""
    quote: str
    quote_index: int
    total_quotes: int


@activity.defn
async def get_random_monty_python_quote() -> QuoteResult:
    """Get a random Monty Python quote."""
    quotes = [
        #Monty Python quotes
        "And now for something completely different.",
        "Nobody expects the Spanish Inquisition!",
        "It's just a flesh wound.",
        "We are the Knights who say... Ni!",
        "What is the airspeed velocity of an unladen swallow?",
        "This parrot is no more! It has ceased to be!",
        "Always look on the bright side of life.",
        "We're not dead yet!",
        "Bring out your dead!",
        "Strange women lying in ponds distributing swords is no basis for government!",
        # Douglas Adams quotes
        "Don't Panic.",
        "The answer to life, the universe, and everything is 42.",
        "So long, and thanks for all the fish.",
        "Time is an illusion. Lunchtime doubly so.",
        "I love deadlines. I love the whooshing noise they make as they go by.",
        "In the beginning the Universe was created. This has made a lot of people very angry and been widely regarded as a bad move.",
    ]
    
    quote_index = random.randint(0, len(quotes) - 1)
    
    return QuoteResult(
        quote=quotes[quote_index],
        quote_index=quote_index,
        total_quotes=len(quotes)
    )