import { useParams } from "react-router-dom";

export default function CardDetail() {
  const { id } = useParams<{ id: string }>();

  return (
    <div>
      <h1 className="text-2xl font-bold">Card Detail</h1>
      <p className="mt-2 text-muted-foreground">
        Viewing analysis card: {id}
      </p>
    </div>
  );
}

