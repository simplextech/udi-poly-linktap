# LinkTap NodeServer

#### Installation

Install through the Polyglot store procedure

#### Requirements

Polyglot running on rPi, Polisy or Polyglot Cloud

## Configuration
 - Requires LinkTap user account
 - Requires LinkTap API Key available by login here:
   - [API Setup](https://www.link-tap.com/#!/api-for-developers)
 - API Limitations
   - LinkTap Rate limits calls to 1 per minute (60 seconds).  Trying to make
   more calls during this time period will result in an error in the logs stating
   a rate limit error
   - Long Poll configuration defaults to 15 minutes (900 seconds).  Minimum is 5 minutes (300 seconds)
     - Long Poll updates online status, battery, signal
   - Short Poll runs at 30 second intervals and updates the watering status
 
## Usage
This Nodeserver provides status information of the LinkTap devices and can also
be used in programs for watering schedules.

- Basic features are
  - instant On (up to 120 minutes)
  - Instant Off
  - Set Watering Modes
    - Interval Mode
    - Odd-Even Mode
    - Seven Day Mode
    - Month Mode

- API Documentation of calls
[LinkTap API](https://www.link-tap.com/#!/api-for-developers)