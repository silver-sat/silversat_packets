from skyfield.api import load, EarthSatellite, wgs84
import matplotlib.pyplot as plt
import numpy as np
import io
import base64
from datetime import datetime, timedelta
import pytz

def find_next_passes(satellite, observer, ts, count=3, min_elevation=10.0):
    now = datetime.now(pytz.UTC)
    t0 = ts.utc(now)
    passes = []
    hours = 0

    while len(passes) < count and hours < 72:
        t1 = ts.utc(now + timedelta(hours=hours + 6))
        t_events, events = satellite.find_events(observer, t0, t1, altitude_degrees=min_elevation)

        i = 0
        while i + 2 < len(events):
            if events[i] == 0 and events[i+1] == 1 and events[i+2] == 2:
                max_elev_time = t_events[i+1] 
                alt, _, _ = (satellite - observer).at(max_elev_time).altaz() 
                max_elev_deg = alt.degrees 
                passes.append((t_events[i], t_events[i+1], t_events[i+2], max_elev_deg))
                if len(passes) == count:
                    break
                i += 3
            else:
                i += 1

        # Advance t0 to just after the last event we processed
        if len(t_events) > 0:
            t0 = t_events[-1].utc_datetime() + timedelta(seconds=1)
            t0 = ts.utc(t0)
        else:
            # If no events found, just move forward by 6 hours
            t0 = t1

        hours += 6


    if not passes:
        raise ValueError("No visible passes found in the next 72 hours.")
    return passes

def generate_orbit_plots(tle1, tle2, lat, lon, elev, timezone_str="UTC"):
    ts = load.timescale()
    satellite = EarthSatellite(tle1, tle2, 'SAT', ts)
    observer = wgs84.latlon(lat, lon, elevation_m=elev)

    # Validate timezone
    try:
        tz = pytz.timezone(timezone_str)
    except pytz.UnknownTimeZoneError:
        tz = pytz.UTC

    passes = find_next_passes(satellite, observer, ts, count=3)
    next_pass = passes[0]
    aos_utc = next_pass[0].utc_datetime().replace(tzinfo=pytz.UTC)
    los_utc = next_pass[2].utc_datetime().replace(tzinfo=pytz.UTC)
    now_utc = datetime.now(pytz.UTC)
    countdown_sec = int((aos_utc - now_utc).total_seconds())

    # Plotting
    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot(111, polar=True)

    for aos, max_elev, los, max_elev_deg in passes:
        times = ts.utc(np.linspace(aos.utc_datetime(), los.utc_datetime(), 100))
        altitudes = []
        azimuths = []

        for t in times:
            difference = satellite - observer
            topocentric = difference.at(t)
            alt, az, _ = topocentric.altaz()
            altitudes.append(alt.degrees)
            azimuths.append(az.degrees)

        az_rad = np.radians(azimuths)
        alt_inv = [90 - a for a in altitudes]
        aos_local = aos.utc_datetime().replace(tzinfo=pytz.UTC).astimezone(tz)
        label = aos_local.strftime('%H:%M %Z')
        ax.plot(az_rad, alt_inv, label=label)

    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    ax.set_rlim(0, 90)
    ax.set_title("Upcoming Visible Passes")
    ax.legend(loc='lower left', fontsize='small')

    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    skyplot_b64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    
    pass_list = [] 
    for aos, max_elev, los, max_elev_deg in passes:
        aos_dt = aos.utc_datetime().replace(tzinfo=pytz.UTC).astimezone(tz) 
        los_dt = los.utc_datetime().replace(tzinfo=pytz.UTC).astimezone(tz) 
        duration = (los_dt - aos_dt).total_seconds() 
        pass_list.append({ 
            "aos": aos_dt.isoformat(), 
            "los": los_dt.isoformat(), 
            "duration": int(duration), 
            "max_elevation_deg": round(max_elev_deg, 1) 
        })

    return { 
        "skyplot": skyplot_b64, 
        "aos": aos_utc.isoformat(), 
        "los": los_utc.isoformat(), 
        "countdown": countdown_sec, 
        "passes": pass_list 
    }
