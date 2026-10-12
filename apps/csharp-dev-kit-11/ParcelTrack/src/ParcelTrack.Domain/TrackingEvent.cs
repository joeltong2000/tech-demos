namespace ParcelTrack.Domain;

public sealed record TrackingEvent(
    DateTimeOffset Timestamp,
    string Location,
    ParcelStatus Status,
    string? Note = null);
