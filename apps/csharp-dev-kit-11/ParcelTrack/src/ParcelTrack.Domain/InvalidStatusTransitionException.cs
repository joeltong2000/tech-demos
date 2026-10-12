namespace ParcelTrack.Domain;

public sealed class InvalidStatusTransitionException(string reference, ParcelStatus from, ParcelStatus to)
    : InvalidOperationException($"Parcel '{reference}' cannot move from {from} to {to}.")
{
    public string Reference { get; } = reference;

    public ParcelStatus From { get; } = from;

    public ParcelStatus To { get; } = to;
}
