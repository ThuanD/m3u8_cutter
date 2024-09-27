import argparse
import subprocess

import requests
from urllib.parse import urljoin
from typing import List


def time_to_seconds(time_str: str) -> int:
    """Convert time in hh:mm:ss format to seconds."""
    try:
        h, m, s = map(int, time_str.split(":"))
        return h * 3600 + m * 60 + s
    except ValueError:
        raise ValueError("Invalid time format. Use hh:mm:ss.")


def parse_m3u8(url: str, start_time: str, end_time: str, output_file: str) -> None:
    """Parse m3u8 file and filter based on time range."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to download m3u8 file from {url}: {e}")
        return

    lines = response.text.splitlines()
    base_url = urljoin(url, ".")

    start_seconds = time_to_seconds(start_time)
    end_seconds = time_to_seconds(end_time)

    if start_seconds >= end_seconds:
        raise ValueError("Start time must be before end time.")

    filtered_segments = filter_segments(lines, start_seconds, end_seconds)
    write_output(output_file, filtered_segments, base_url)


def filter_segments(lines: List[str], start_seconds: int, end_seconds: int) -> List[str]:
    """Filter segments based on the given time range."""
    total_time = 0
    inside_range = False
    result = []
    add_start = True

    # Loop through each line of the m3u8 file
    for i, line in enumerate(lines):
        line = line.strip()
        if line.startswith("#EXTINF"):
            add_start = False
            # Extract duration of the video segment from EXTINF
            duration = float(line.split(":")[1].rstrip(","))

            # Start recording segments once the total time exceeds the start time
            if total_time >= start_seconds:
                inside_range = True

            # Stop recording if the total time exceeds the end time
            if total_time >= end_seconds:
                break

            # Accumulate the total time passed
            total_time += duration

            # If the segment is within the desired time range, add EXTINF line to the result
            if inside_range:
                result.append(line)

        if add_start:
            result.append(line)

        # If inside the desired time range, append the .ts file with the base URL
        if inside_range and line.endswith(".ts"):
            result.append(line)

    return result


def write_output(output_file: str, filtered_segments: List[str], base_url: str) -> None:
    """Write the filtered segments to a new m3u8 file."""
    with open(output_file, "w") as output:
        for line in filtered_segments:
            if line.endswith(".ts"):
                output.write(f"{base_url}/{line}\n")
            else:
                output.write(f"{line}\n")

        output.write("#EXT-X-ENDLIST\n")

    print(f"New m3u8 file saved as {output_file}")


# Function to convert the m3u8 file to mp4 using ffmpeg
def convert_to_mp4(m3u8_file, output_mp4):
    # ffmpeg command to convert m3u8 to mp4
    command = [
        "ffmpeg",
        "-y",
        "-protocol_whitelist", "file,http,https,tcp,tls,crypto",
        "-i", m3u8_file,
        "-c", "copy",
        "-bsf:a", "aac_adtstoasc",
        output_mp4
    ]

    # Run the ffmpeg command
    try:
        subprocess.run(command, check=True)
        print(f"Conversion complete: {output_mp4}")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred during conversion: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Process m3u8 file from URL with specific time range.")
    parser.add_argument("-u", "--url", type=str, required=True,
                        help="URL of the m3u8 file")
    parser.add_argument("-s", "--start_time", type=str, required=True,
                        help="Start time in format hh:mm:ss")
    parser.add_argument("-e", "--end_time", type=str, required=True,
                        help="End time in format hh:mm:ss")
    parser.add_argument("-o", "--output_file", type=str, required=True,
                        help="Name of the output m3u8 file")
    parser.add_argument("-c", "--convert", type=bool, required=False, default=False,
                        help="Name of the output m3u8 file")

    args = parser.parse_args()

    try:
        parse_m3u8(args.url, args.start_time, args.end_time, args.output_file)
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    if args.convert:
        # Convert the newly created m3u8 file to mp4
        output_mp4 = args.output_file.replace(".m3u8", ".mp4")
        convert_to_mp4(args.output_file, output_mp4)


if __name__ == "__main__":
    main()
