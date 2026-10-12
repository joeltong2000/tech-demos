using ParcelTrack.Application;
using ParcelTrack.Domain;

namespace ParcelTrack.Infrastructure;

public sealed class InMemoryParcelRepository : IParcelRepository
{
    private readonly Dictionary<string, Parcel> _parcels = new(StringComparer.OrdinalIgnoreCase);
    private readonly Lock _lock = new();

    public Parcel? Find(string reference)
    {
        lock (_lock)
        {
            return _parcels.GetValueOrDefault(reference);
        }
    }

    public IReadOnlyList<Parcel> All()
    {
        lock (_lock)
        {
            return [.. _parcels.Values];
        }
    }

    public void Add(Parcel parcel)
    {
        lock (_lock)
        {
            _parcels.Add(parcel.Reference, parcel);
        }
    }
}
