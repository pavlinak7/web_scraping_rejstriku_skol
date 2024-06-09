import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from matplotlib import cm, colors
import json

# Load the data
celk_df = pd.read_csv("celk_df_f.csv", sep="#")

# Drop rows with None values in 'Coordinates'
celk_df = celk_df.dropna(subset=['Coordinates'])
celk_df['Coordinates'] = celk_df['Coordinates'].apply(eval)

# Identify all nazev columns
nazev_columns = [col for col in celk_df.columns if col.startswith('nazev') and col != 'nazev']

# Collect unique values from all nazev columns
unique_nazev_values = pd.unique(celk_df[nazev_columns].values.ravel('K'))
unique_nazev_values = [val for val in unique_nazev_values if pd.notna(val)]

# Generate a list of unique colors
unique_zrizovatel = celk_df['zrizovatel_dropdown'].unique()
colormap = cm.get_cmap('tab10', len(unique_zrizovatel))
color_list = [colors.rgb2hex(colormap(i)[:3]) for i in range(len(unique_zrizovatel))]

# Map each zrizovatel to a color
zrizovatel_color_map = dict(zip(unique_zrizovatel, color_list))

# Streamlit app
st.title('Vizualizace informací z rejstříku škol')

# Initialize session state for map center and zoom
if 'map_center' not in st.session_state:
    st.session_state.map_center = [49.8175, 15.4730]
if 'map_zoom' not in st.session_state:
    st.session_state.map_zoom = 7
if 'last_selected_region' not in st.session_state:
    st.session_state.last_selected_region = 'All'

# Define center coordinates for each region
region_centers = {
    "Hlavní město Praha": [50.06678964987252, 14.465998829962977],
    "Středočeský kraj": [50.003605191950115, 14.54954836371052],
    "Jihočeský kraj": [49.09310368241909, 14.432286603192251],
    "Plzeňský kraj": [49.59818612785983, 13.228010116617472],
    "Karlovarský kraj": [50.1740783270064, 12.753140604283816],
    "Ústecký kraj": [50.53040763516859, 13.84565561762281],
    "Liberecký kraj": [50.70495750261212, 14.99864445395474],
    "Královéhradecký kraj": [50.383626410733015, 15.866464780805817],
    "Pardubický kraj": [49.90127803525259, 16.191215444747982],
    "Kraj Vysočina": [49.41344724547589, 15.671506555415327],
    "Jihomoravský kraj": [49.08016770385136, 16.635192353088943],
    "Olomoucký kraj": [49.77734134610242, 17.19105583754125],
    "Moravskoslezský kraj": [49.82068318540236, 17.979370693046423],
    "Zlínský kraj": [49.22046625560532, 17.747374912706007]
}

# Add a dropdown menu for regions
unique_regions = celk_df['Region'].unique()
selected_region = st.selectbox('Vyber kraj', options=['All'] + list(unique_regions), index=0)

# Update the map center and zoom level only if the region has changed
if selected_region != st.session_state.last_selected_region:
    if selected_region != 'All' and selected_region in region_centers:
        st.session_state.map_center = region_centers[selected_region]
        st.session_state.map_zoom = 9  # Adjust zoom level as needed
    else:
        st.session_state.map_center = [49.8175, 15.4730]
        st.session_state.map_zoom = 7  # Default zoom level
    st.session_state.last_selected_region = selected_region

# Filter the DataFrame based on the selected region to find relevant zrizovatel
regional_df = celk_df[celk_df['Region'] == selected_region] if selected_region != 'All' else celk_df
region_specific_zrizovatel = regional_df['zrizovatel_dropdown'].unique()

# Add a multiselect menu for zrizovatel
selected_zrizovatel = st.multiselect('Vyber zřizovatele školy', options=['All'] + list(region_specific_zrizovatel), default=['All'])

# Add a multiselect menu for nazev values
selected_nazev_values = st.multiselect('Vyber typ školy', options=['All'] + unique_nazev_values, default=['All'])

# Filter the DataFrame based on the selected zrizovatel values
if 'All' not in selected_zrizovatel:
    filtered_df = regional_df[regional_df['zrizovatel_dropdown'].isin(selected_zrizovatel)]
else:
    filtered_df = regional_df

# Further filter the DataFrame based on the selected nazev values
if 'All' not in selected_nazev_values:
    filtered_df = filtered_df[filtered_df[nazev_columns].apply(lambda row: any(val in selected_nazev_values for val in row), axis=1)]

# Display the number of filtered points
number_of_schools = len(filtered_df)
st.write(f"počet vybraných škol: {number_of_schools}")

# Create the map with the stored center and zoom level
map = folium.Map(location=st.session_state.map_center, zoom_start=st.session_state.map_zoom)

# Load the GeoJSON data
def load_geojson(path):
    with open(path) as f:
        geojson_data = json.load(f)
    return geojson_data

# Add a checkbox for displaying the GeoJSON layer
show_geojson = st.checkbox('Zobrazit hranice krajů')

def style_function(feature):
    return {
        'fillColor': 'none',
        'color': 'blue',
        'weight': 2
    }

if show_geojson:
    geojson_path = "kraje.json"
    geojson_data = load_geojson(geojson_path)
    folium.GeoJson(
        geojson_data,
        name='geojson',
        style_function=style_function
    ).add_to(map)

# Add points to the map with different colors
for index, row in filtered_df.iterrows():
    items = [f"<li>{row[col]}</li>" for col in nazev_columns if pd.notna(row[col])]
    items_str = "".join(items)
    popup_content = f"""
    <b style="font-size:16px;">{row['nazev']}</b><br>
    <strong style="font-size:14px;">Zřizovatel: {row['zrizovatel_dropdown']}</strong><br>
    <ul style="font-size:12px;">
        {items_str}
    </ul>
    """
    folium.CircleMarker(
        location=row['Coordinates'],
        radius=4,  # Adjust the radius as needed
        popup=folium.Popup(popup_content, max_width=300),
        color=zrizovatel_color_map[row['zrizovatel_dropdown']],  # Border color
        fill=True,
        fill_color=zrizovatel_color_map[row['zrizovatel_dropdown']],  # Fill color
        fill_opacity=1  # Adjust the fill opacity as needed
    ).add_to(map)

# Add layer control to toggle the GeoJSON layer
folium.LayerControl().add_to(map)

# Display the map and get the map state
map_state = st_folium(map, width=700, height=500)

# Update the session state with the current map center and zoom level
if map_state and 'center' in map_state and 'zoom' in map_state:
    st.session_state.map_center = [map_state['center']['lat'], map_state['center']['lng']]
    st.session_state.map_zoom = map_state['zoom']

