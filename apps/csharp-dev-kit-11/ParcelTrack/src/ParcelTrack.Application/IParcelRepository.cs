using ParcelTrack.Domain;

namespace ParcelTrack.Application;

public interface IParcelRepository
{
    Parcel? Find(string reference);

    IReadOnlyList<Parcel> All();

    void Add(Parcel parcel);
}
