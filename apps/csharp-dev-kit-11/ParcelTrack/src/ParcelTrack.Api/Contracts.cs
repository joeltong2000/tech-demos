using ParcelTrack.Domain;

namespace ParcelTrack.Api;

public sealed record RegisterParcelRequest(string Reference, string Recipient, string Destination);

public sealed record RecordEventRequest(ParcelStatus Status, string Location, string? Note = null);

public sealed record ParcelResponse(
    string Reference,
    string Recipient,
    string Destination,
    ParcelStatus Status,
    IReadOnlyList<TrackingEvent> Events)
{
    public static ParcelResponse From(Parcel parcel) =>
        new(parcel.Reference, parcel.Recipient, parcel.Destination, parcel.Status, parcel.Events);
}
