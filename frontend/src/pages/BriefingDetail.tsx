import { useParams } from "react-router-dom";

export default function BriefingDetail() {
  const { id } = useParams<{ id: string }>();

  return (
    <div>
      <h1 className="text-2xl font-bold">Briefing Detail</h1>
      <p className="mt-2 text-muted-foreground">
        Viewing briefing: {id}
      </p>
    </div>
  );
}

