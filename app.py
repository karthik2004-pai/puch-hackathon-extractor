
import anyio

import click

import mcp.types as types

from mcp.server.lowlevel import Server

@click.command()

@click.option("--port", default=8000, help="Port to listen on for SSE")

@click.option(

    "--transport",

    type=click.Choice(["stdio", "sse"]),

    default="stdio",

    help="Transport type",

)

def main(port: int, transport: str) -> int:

    app = Server("mcp-info-extractor-server")

    @app.call_tool()

    async def run_tool(name: str, arguments: dict) -> list[types.ContentBlock]:

        if name != "info-extractor":

            raise ValueError(f"Unknown tool: {name}")

        if "text" not in arguments:

            raise ValueError("Missing required argument 'text'")

        

        input_text = arguments.get("text", "")

       

        char_count = len(input_text)

        words = input_text.split()

        word_count = len(words)

     

        sentence_count = input_text.count('.') + input_text.count('!') + input_text.count('?')

       

        reading_time_minutes = round(word_count / 200, 2)

        

        result_string = (

            f"--- Analysis Complete ---\n"

            f"Character Count: {char_count}\n"

            f"Word Count: {word_count}\n"

            f"Sentence Count: {sentence_count}\n"

            f"Estimated Reading Time: {reading_time_minutes} minutes"

        )

        

       

        return [types.TextContent(type="text", text=result_string)]

    @app.list_tools()

    async def list_tools() -> list[types.Tool]:

        return [

            types.Tool(

                name="info-extractor",

                title="Information Extractor",

                description="Extracts key information from any text.",

                inputSchema={

                    "type": "object",

                    "required": ["text"],

                    "properties": {

                        "text": {

                            "type": "string",

                            "description": "The block of text to analyze.",

                        }

                    },

                },

            )

        ]

    if transport == "sse":

        from mcp.server.sse import SseServerTransport

        from starlette.applications import Starlette

        from starlette.responses import Response

        from starlette.routing import Mount, Route

        sse = SseServerTransport("/messages/")

        async def handle_sse(request):

            async with sse.connect_sse(

                request.scope, request.receive, request._send

            ) as streams:

                await app.run(

                    streams[0], streams[1], app.create_initialization_options()

                )

            return Response()

        starlette_app = Starlette(

            debug=True,

            routes=[

                Route("/sse", endpoint=handle_sse, methods=["GET"]),

                Mount("/messages/", app=sse.handle_post_message),

            ],

        )

        import uvicorn

        uvicorn.run(starlette_app, host="127.0.0.1", port=port)

    else:

        from mcp.server.stdio import stdio_server

        async def arun():

            async with stdio_server() as streams:

                await app.run(

                    streams[0], streams[1], app.create_initialization_options()

                )

        anyio.run(arun)

    return 0



if __name__ == "__main__":

    main()



