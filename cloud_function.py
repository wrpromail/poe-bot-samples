import fastapi_poe as fp 

class EchoBot(fp.PoeBot):
    async def get_response(self, request: fp.QueryRequest):
        last_message = request.query[-1].content 
        yield fp.PartialResponse(text=last_message)

if __name__ == "__main__":
    fp.run(EchoBot(), allow_without_key=True)