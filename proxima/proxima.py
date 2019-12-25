import asyncio
import pyttsx3

def sayit(message,role):
    engine = pyttsx3.init()
    if role == 'server':
        engine.setProperty('voice', 'com.apple.speech.synthesis.voice.tessa')
    engine.say(message)
    engine.runAndWait()

# An Artemis proxy for the enhancement of various interactions and game controls. 

async def conduit(reader, writer,role):
    try:
        while not reader.at_eof():
            proxy_action = sayit
            data = await reader.read(2048)
            print("received from {}: {}".format(role,data.decode()))
            proxy_action(data.decode(),role)
            writer.write(data)
    finally:
        writer.write("Closing connection".encode()) 
        writer.close()


async def handle_client(local_reader, local_writer,):
    try:
        remote_reader, remote_writer = await asyncio.open_connection('127.0.0.1', 2010)
        pipe1 = conduit(local_reader, remote_writer,"client")
        pipe2 = conduit(remote_reader, local_writer,"server")
        await asyncio.gather(pipe1, pipe2)
    finally:
        local_writer.close()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    coro = asyncio.start_server(handle_client, '127.0.0.1', 22010)
    server = loop.run_until_complete(coro)
    print('Listening on {}'.format(server.sockets[0].getsockname()))
    loop.run_forever()

    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()
