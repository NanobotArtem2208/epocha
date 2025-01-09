import asyncio
import aiohttp
import time


async def fetch_products():
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://nanobotartem2208-epocha-0ed6.twc1.net/api/products"
        ) as response:
            if response.status == 200:
                data = await response.json()
                print(f"Received {len(data['Products'])} products")
            else:
                print(f"Error fetching products: {response.status}")


async def main():
    start_time = time.time()
    tasks = []
    num = 0
    for _ in range(10000):
        tasks.append(await fetch_products())
        num += 1
        print(f"{num} запрос")
    await asyncio.gather(*tasks)
    end_time = time.time()
    print(f"Total time: {end_time - start_time:.2f} seconds")


if __name__ == "__main__":
    asyncio.run(main())
