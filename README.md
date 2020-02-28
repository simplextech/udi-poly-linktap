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
   more calles during this time period will result in an error in the logs stating
   a rate limit error
   - Long Poll configuration defaults to 300 seconds (5 minutes).  If you lower this to the 
   minimum of 60 seconds you can only make 1 command call or status call during that
   1 minute time frame.
 
## Usage
This Nodeserver provides status information of the LinkTap devices and can also
be used in programs for watering schedules.

- Basic features are
  - instant on (0 minutes is Off, any other value is On)
  - Set Watering Modes
    - Interval Mode
    - Odd-Even Mode
    - Seven Day Mode
    - Month Mode

- API Documentation of calls
[LinkTap API](https://www.link-tap.com/#!/api-for-developers)