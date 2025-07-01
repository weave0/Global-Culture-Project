# Global Culture Project Documentation

## New Fields in `.v3.json` Stubs

### `estimated_speakers`

- **Description**: A rough estimate of the number of native speakers of the language.
- **Example**: `"485 million"`
- **Source**: Wikipedia or Ethnologue

### `primary_regions`

- **Description**: A list of countries or regions where the language is widely spoken.
- **Example**: `["Spain", "Mexico", "Colombia", "Argentina", "Peru", "United States"]`
- **Note**: This list is not exhaustive; cultural relevance is prioritized.

### Example `.v3.json` Stub

```json
{
  "culture_name": "Spanish",
  "language_tag": "es",
  "estimated_speakers": "485 million",
  "primary_regions": ["Spain", "Mexico", "Colombia", "Argentina", "Peru", "United States"],
  ...
}
```

## Usage

The `gpt_enrich_fields.py` script has been updated to include these new fields from the `language_population_data.json` file. The script will automatically enrich the `.v3.json` stubs with the `estimated_speakers` and `primary_regions` fields if they are available in the JSON file.

## Contact

For any questions or issues, please contact the project maintainer.
