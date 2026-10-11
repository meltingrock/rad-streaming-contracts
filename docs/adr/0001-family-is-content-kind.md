# Family is the content kind, not how an item was placed

`family` on HourPlan items and channel events is a closed enum owned by this contract, and it says what kind of content an item is (music, advert, station ID, ...), never how the item got into the plan. Advertiser proof of airing and royalty returns filter as-run entries on `family`, and those entries are kept for 5 years, so the value has to mean one thing. How an item was placed is already carried by its placing schedule (`PRC-` / `MESC-` code) or clock segment, so `family` does not repeat it.

## Consequences

- `prerec` is not a family. A prerec schedule's compiled media is an advert, so `PRC-` items carry `advert`. This reverses the playout RPC's earlier choice of `"prerec"` "so a plan says where an item came from"; the placing schedule now says that.
- The media's own family wins over the slot's: a station ID in a music segment's playlist is `station_id`, not `music`. The clock segment or schedule `media_family` is only a fallback.
- Values: `music, advert, announcement, special, promo, news, weather, traffic, station_id, sweeper, presenter_link, psa, feature, sponsorship_bumper, other`. `rad-api-schedules` and `rad-api-media` validate against this list.
- The compiler maps an unrecognised source value to `other`, keeps the original in `family_source`, and warns. The wire only ever carries listed values, and an `other` entry can still be reclassified later.
- Introducing the enum is contract 2.0.0 (HourPlan `schema_version` `2.0`). Adding a value later is a minor release (consumers before the compiler); removing one is major.

## Considered Options

- **Family as source** (`prerec`, segment slot): rejected; it duplicates the placing schedule and hides whether an advert or a track aired.
- **Reject unknown values** instead of mapping them to `other`: rejected in favour of `other` plus `family_source`, so the item still airs and its as-run entry still exists.
