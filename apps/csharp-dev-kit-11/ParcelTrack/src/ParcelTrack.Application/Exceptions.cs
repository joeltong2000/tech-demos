namespace ParcelTrack.Application;

public sealed class DuplicateParcelException(string reference)
    : InvalidOperationException($"A parcel with reference '{reference}' already exists.")
{
    public string Reference { get; } = reference;
}

public sealed class ParcelNotFoundException(string reference)
    : KeyNotFoundException($"No parcel with reference '{reference}' was found.")
{
    public string Reference { get; } = reference;
}
