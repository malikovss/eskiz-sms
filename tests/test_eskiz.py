import asyncio
import logging
import os

from dotenv import load_dotenv

from eskiz_sms.async_ import EskizSMS

load_dotenv()
logging.basicConfig(level=logging.DEBUG)

eskiz = EskizSMS(
    email=os.getenv('EMAIL'),
    password=os.getenv('PASSWORD'),
    save_token=True,
    auto_update_token=True
)
eskiz.token.set(os.getenv('ESKIZ_TOKEN'))


async def main():
    response = await eskiz.get_limit()
    print(response)


if __name__ == '__main__':
    # main()
    asyncio.run(main())
