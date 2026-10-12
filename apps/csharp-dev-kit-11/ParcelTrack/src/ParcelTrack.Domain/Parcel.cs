namespace ParcelTrack.Domain;

public sealed class Parcel
{
    private readonly List<TrackingEvent> _events = [];

    public Parcel(string reference, string recipient, string destination)
    {
        if (string.IsNullOrWhiteSpace(reference))
        {
            throw new ArgumentException("Reference is required.", nameof(reference));
        }

        if (string.IsNullOrWhiteSpace(recipient))
        {
            throw new ArgumentException("Recipient is required.", nameof(recipient));
        }

        Reference = reference.ToUpperInvariant();
        Recipient = recipient;
        Destination = destination;
        Status = ParcelStatus.Registered;
        _events.Add(new TrackingEvent(DateTimeOffset.UtcNow, "Origin depot", ParcelStatus.Registered, "Parcel registered"));
    }

    public string Reference { get; }

    public string Recipient { get; }

    public string Destination { get; }

    public ParcelStatus Status { get; private set; }

    public IReadOnlyList<TrackingEvent> Events => _events;

    public TrackingEvent RecordEvent(ParcelStatus newStatus, string location, string? note = null)
    {
        if (!IsValidTransition(Status, newStatus))
        {
            throw new InvalidStatusTransitionException(Reference, Status, newStatus);
        }

        var trackingEvent = new TrackingEvent(DateTimeOffset.UtcNow, location, newStatus, note);
        _events.Add(trackingEvent);
        Status = newStatus;
        return trackingEvent;
    }

    public static bool IsValidTransition(ParcelStatus from, ParcelStatus to) => from switch
    {
        ParcelStatus.Registered => to is ParcelStatus.InTransit,
        ParcelStatus.InTransit => to is ParcelStatus.InTransit or ParcelStatus.OutForDelivery or ParcelStatus.ReturnedToSender,
        ParcelStatus.OutForDelivery => to is ParcelStatus.Delivered or ParcelStatus.InTransit or ParcelStatus.ReturnedToSender,
        ParcelStatus.Delivered => false,
        ParcelStatus.ReturnedToSender => false,
        _ => throw new ArgumentOutOfRangeException(nameof(from), from, "Unknown parcel status."),
    };
}
