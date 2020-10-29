# Pi-Scan
Convert a Raspberry Pi (or Linux device) into a headless scanner station.

# Usage
Write a callback function that should be called every time something is scanned.
Then, create a `Listener` object and pass it your callback function, like so:
```python
from pi_scan import Listener

def your_callback(scanned_string: str):
	print(f"You scanned --> {scanned_string}")

listener = Listener(callback=your_callback)

# Start the scanners. This method will never exit.
listener.listen()
```
When something is scanned, a new thread is created running the passed callback;
the only argument passed is the string that was scanned. A scan is determined to
have happened when a separator character is encountered, which by default is
either Enter or Tab. At that point, all the typed characters between the last
separator and the just encountered separator are joined together and passed to
the callback.
