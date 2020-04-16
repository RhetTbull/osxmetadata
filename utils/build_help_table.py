""" Builds the attributes table in markdown format for README.md """

import osxmetadata

print("| Constant | Short Name | Long Constant | Description |")
print("|---------------|----------|---------|-----------|")
for attribute in sorted(
    [
        attribute_name
        for attribute_name in {
            osxmetadata.ATTRIBUTES[attr].name for attr in sorted(osxmetadata.ATTRIBUTES)
        }
    ]
):
    attr = osxmetadata.ATTRIBUTES[attribute]
    help_ = attr.api_help if attr.api_help is not None else attr.help
    print(f"|{attr.short_constant}|{attr.name}|{attr.constant}|{help_}|")
