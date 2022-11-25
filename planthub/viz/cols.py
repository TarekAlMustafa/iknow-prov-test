# TODO: Read excel table and convert to dataframe (.pickle) in /data
# TODO: Use dataframe instead of CAT_COLS and CONT_COLS

CAT_COLS = {
    "TRY": [
        ("AccFamily", "AccFamily", "AccFamily DE", "Description"),
        ("AccGenus", "AccGenus", "AccGenus DE", "Description"),
        ("TRY_Dispersal syndrome", "Dispersal syndrome", "Dispersal syndrome DE", "Description"),
        ("TRY_Growth form 1", "Growth form 1", "Growth form 1 DE", "Description"),
        ("TRY_Leaf shape", "Leaf shape", "Leaf shape DE", "Description"),
        ("TRY_Leaf tip", "Leaf tip", "Leaf tip DE", "Description"),
        ("TRY_Leaf phenology type", "Leaf phenology type", "Leaf phenology type DE", "Description"),
        ("TRY_Pollination syndrome", "Pollination syndrome", "Pollination syndrome DE", "Description"),
        ("TRY_Woodiness", "Woodiness", "Woodiness DE", "Description")
    ],
    "PhenObs": [
        ("AccFamily", "AccFamily", "AccFamily DE", "Description"),
        ("AccGenus", "AccGenus", "AccGenus DE", "Description"),
        ("AccSpeciesName", "AccSpeciesName", "AccSpeciesName DE", "Description"),
        ("Botanic_Garden_Name", "Botanic Garden Name", "Botanic Garden Name DE", "Description")
    ]
}

CONT_COLS = {
    "TRY": [
        ("Latitude_WGS84", "Latitude_WGS84", "Latitude_WGS84 DE", "Description"),
        ("TRY_Dispersal unit dry mass", "Dispersal unit dry mass", "Dispersal unit dry mass DE", "Description"),
        ("TRY_Leaf (length^2)/area", "Leaf (length^2)/area", "Leaf (length^2)/area DE", "Description"),
        ("TRY_Leaf area", "Leaf area", "Leaf area DE", "Description"),
        ("TRY_Leaf (perimeter^2)/area", "Leaf (perimeter^2)/area", "Leaf (perimeter^2)/area DE", "Description"),
        ("TRY_Leaf perimeter/area", "Leaf perimeter/area", "Leaf perimeter/area DE", "Description"),
        ("TRY_Plant height generative", "Plant height generative", "Plant height generative DE", "Description"),
        ("TRY_Plant height vegetative", "Plant height vegetative", "Plant height vegetative DE", "Description"),
        ("TRY_Plant relative growth rate (RGR)", "Plant relative growth rate (RGR)",
         "Plant relative growth rate (RGR) DE", "Description"),
        ("TRY_Stomata density", "Stomata density", "Stomata density DE", "Description")
    ],
    "PhenObs": [
        ("C_N_ratio_garden", "C_N_ratio_garden", "C_N_ratio_garden DE", "Description"),
        ("Latitude_WGS84", "Latitude_WGS84", "Latitude_WGS84 DE", "Description"),
        ("veg_height_garden_cm", "veg_height_garden_cm", "veg_height_garden_cm DE", "Description")
    ]
}


def all_cols():
    allcols = []
    for df in CAT_COLS.values():
        for col in df:
            if col not in allcols:
                allcols.append(col)

    for df in CONT_COLS.values():
        for col in df:
            if col not in allcols:
                allcols.append(col)

    return allcols
