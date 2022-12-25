import asyncio
import os

from dotenv import load_dotenv

from eskiz_sms.async_ import EskizSMS

load_dotenv()

eskiz = EskizSMS(
    email=os.getenv('EMAIL'),
    password=os.getenv('PASSWORD'),
    save_token=True,
)


async def main():
    response = await eskiz.get_limit()
    print(response)


if __name__ == '__main__':
    # main()
    asyncio.run(main())
