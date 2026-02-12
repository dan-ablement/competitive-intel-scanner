import { useParams } from "react-router-dom";

export default function CompetitorDetail() {
  const { id } = useParams<{ id: string }>();

  return (
    <div>
      <h1 className="text-2xl font-bold">Competitor Detail</h1>
      <p className="mt-2 text-muted-foreground">
        Viewing competitor profile: {id}
      </p>
    </div>
  );
}

