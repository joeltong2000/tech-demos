using ParcelTrack.Domain;

namespace ParcelTrack.Application;

public sealed class ParcelService(IParcelRepository repository)
{
    public Parcel Register(string reference, string recipient, string destination)
    {
        if (repository.Find(reference) is not null)
        {
            throw new DuplicateParcelException(reference);
        }

        var parcel = new Parcel(reference, recipient, destination);
        repository.Add(parcel);
        return parcel;
    }

    public Parcel? Find(string reference) => repository.Find(reference);

    public IReadOnlyList<Parcel> All() => repository.All();

    public TrackingEvent RecordEvent(string reference, ParcelStatus status, string location, string? note = null)
    {
        var parcel = repository.Find(reference) ?? throw new ParcelNotFoundException(reference);
        return parcel.RecordEvent(status, location, note);
    }
}
