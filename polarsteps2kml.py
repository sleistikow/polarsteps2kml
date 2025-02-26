# Copyright (c) 2025 Simon Leistikow
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.


import argparse
import json
import os
import zipfile
import xml.etree.ElementTree as ET

kml_boilerplate = '''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2" xmlns:kml="http://www.opengis.net/kml/2.2" xmlns:atom="http://www.w3.org/2005/Atom">
<Document>
	<name>MyTrips.kml</name>
	<StyleMap id="inline">
		<Pair>
			<key>normal</key>
			<styleUrl>#inline1</styleUrl>
		</Pair>
		<Pair>
			<key>highlight</key>
			<styleUrl>#inline0</styleUrl>
		</Pair>
	</StyleMap>
	<Style id="inline0">
		<LineStyle>
			<color>ffffffff</color>
			<width>3</width>
		</LineStyle>
		<PolyStyle>
			<fill>0</fill>
		</PolyStyle>
	</Style>
	<Style id="inline1">
		<LineStyle>
			<color>eeeeeeff</color>
			<width>3</width>
		</LineStyle>
		<PolyStyle>
			<fill>0</fill>
		</PolyStyle>
	</Style>
	<Folder>
		<name>MyTrips</name>
        <open>1</open>
	</Folder>
</Document>
</kml>
'''

kml_trip_template = '''
<Folder>
    <name>##TRIP_NAME##</name>
    <open>1</open>
</Folder>
'''

locations_template = '''
<Placemark>
    <name>Path Measure</name>
    <styleUrl>#inline</styleUrl>
    <LineString>
        <tessellate>1</tessellate>
        <coordinates>
        </coordinates>
    </LineString>
</Placemark>
'''

photo_template = '''
<PhotoOverlay>
    <name>##PHOTO_NAME##</name>
    <description>##PHOTO_DESCRIPTION##</description>
    <Camera>
        <longitude>##PHOTO_LONGITUDE##</longitude>
        <latitude>##PHOTO_LATITUDE##</latitude>
        <altitude>0</altitude>
    </Camera>
    <Style>
        <IconStyle>
            <Icon>
                <href>:/camera_mode.png</href>
            </Icon>
        </IconStyle>
        <ListStyle>
            <listItemType>check</listItemType>
            <ItemIcon>
                <state>open closed error fetching0 fetching1 fetching2</state>
                <href>http://maps.google.com/mapfiles/kml/shapes/camera-lv.png</href>
            </ItemIcon>
            <bgColor>00ffffff</bgColor>
            <maxSnippetLines>2</maxSnippetLines>
        </ListStyle>
    </Style>
    <Icon>
    </Icon>
    <ViewVolume>
    </ViewVolume>
    <Point>
        <coordinates>##PHOTO_LONGITUDE##,##PHOTO_LATITUDE##,0</coordinates>
    </Point>
</PhotoOverlay>
'''


class Trip:

    def __init__(self, root_path):
        self.root_path = root_path

        locations_file = os.path.join(self.root_path, 'locations.json')
        with open(locations_file, 'r') as file:
            locations = json.load(file)
            locations = locations['locations']
            # Sort locations by time.
            locations = sorted(locations, key=lambda x: x['time'])
            self.locations = locations

        trip_file = os.path.join(self.root_path, 'trip.json')
        with open(trip_file, 'r') as file:
            trip_data = json.load(file)
            self.steps = trip_data['all_steps']
            self.name = trip_data['name']
            self.slug = trip_data['slug']
            self.id = trip_data['id']

    def add_locations(self, trip_tree):

        root = ET.fromstring(locations_template)
        coordinates_elem = root.find('.//coordinates')

        coordinates = [
            f'{location["lon"]},{location["lat"]},0' for location in self.locations
        ]

        coordinates_string = '\n'.join(coordinates)
        coordinates_elem.text = coordinates_string

        trip_tree.append(root)

    def add_photos(self, trip_tree):
        for step in self.steps:

            step_id = step['id']
            step_slug = step['slug']

            photo_folder = os.path.join(self.root_path, str(step_slug) + '_' + str(step_id), 'photos')

            foto_paths = []
            if os.path.exists(photo_folder):
                for file in sorted(os.listdir(photo_folder)):
                    foto_paths.append(os.path.join(photo_folder, file))

            description = [f'<img style="max-width:500px;" src="file:///{path}">' for path in foto_paths]
            description = ''.join(description)
            description = f'<![CDATA[{description}<p>{step["description"]}]]>'

            photo_string = photo_template
            photo_string = photo_string.replace('##PHOTO_NAME##', step['display_name'])
            photo_string = photo_string.replace('##PHOTO_DESCRIPTION##', description)
            photo_string = photo_string.replace('##PHOTO_LONGITUDE##', str(step['location']['lon']))
            photo_string = photo_string.replace('##PHOTO_LATITUDE##', str(step['location']['lat']))

            photo_tree = ET.fromstring(photo_string)
            photo_tree.find('.//Camera').append(ET.Element('gx:altitudeMode', text='relativetoSeaFloor'))
            photo_tree.find('.//Point').append(ET.Element('gx:altitudeMode', text='relativetoSeaFloor'))

            trip_tree.append(photo_tree)

    def add_to_kml(self, kml_tree):
        namespaces = {
            'kml': 'http://www.opengis.net/kml/2.2',
            'xmlns:gx': 'http://www.google.com/kml/ext/2.2',
            'xmlns:kml': 'http://www.opengis.net/kml/2.2',
            'xmlns:atom': 'http://www.w3.org/2005/Atom'
        }
        trip_tree_string = kml_trip_template.replace('##TRIP_NAME##', self.name)
        trip_tree = ET.fromstring(trip_tree_string)
        self.add_locations(trip_tree)
        self.add_photos(trip_tree)
        node = kml_tree.find('.//kml:Document/kml:Folder', namespaces)
        node.append(trip_tree)

def extract_archive(archive_path, output_path):
    if not zipfile.is_zipfile(archive_path):
        return archive_path

    print('Extracting archive...')

    directory_path, filename = os.path.split(output_path)
    name, _ = os.path.splitext(filename)
    extracted_archive_path = str(os.path.join(directory_path, name + '_data'))

    with zipfile.ZipFile(archive_path, 'r') as archive:
        os.makedirs(extracted_archive_path, exist_ok=True)
        archive.extractall(extracted_archive_path)

    return extracted_archive_path


def convert_trips(trips_data_path, output_path):
    print('Converting Trips...')
    kml_tree = ET.fromstring(kml_boilerplate)

    trip_folder = os.path.join(trips_data_path, 'trip')
    for folder in sorted(os.listdir(trip_folder)):
        trip_root_path = os.path.join(trip_folder, folder)
        trip = Trip(trip_root_path)
        trip.add_to_kml(kml_tree)
        print(f'...Trip: {trip.name} ({trip.id}) Done.')

    print('Writing KML file...')

    ET.ElementTree(kml_tree).write(output_path, encoding='utf-8', xml_declaration=True)


def convert(archive_path, output_path):
    print('Converting Polarsteps data to KML...')
    trips_data_path = extract_archive(archive_path, output_path)
    convert_trips(trips_data_path, output_path)
    print('Done!')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=
        """
        A script that converts a polarsteps archive (https://www.polarsteps.com) into a kml file, 
        e.g., to be read by Google Earth (https://www.earth.google.com). 
        
        Current limitations include: 
        - Only photos, descriptions, and locations will be included in the output file. 
        - The order of photos per step is not contained in the polarsteps archive and will be lost. 
        - Paths to photos in the kml file are absolute. 
        """
    )

    parser.add_argument("input", help="Path to polarsteps zip archive (may be extracted)")
    parser.add_argument("output", help="Output kml file path (including filename)")

    args = parser.parse_args()

    # Strip single and double quotes.
    input_path = args.input.strip('\'"')
    output_path = args.output.strip('\'"')

    convert(input_path, output_path)
