import { useState } from "react";
import { MessageSquare, Reply, Check, CheckCheck, Send } from "lucide-react";
import { useCardComments, useAddCardComment, useResolveCardComment } from "@/hooks/use-cards";
import type { CardCommentResponse } from "@/api/cards";
import { cn } from "@/lib/utils";

interface CommentsPanelProps {
  cardId: string;
}

function CommentItem({
  comment,
  cardId,
  onReply,
}: {
  comment: CardCommentResponse;
  cardId: string;
  onReply: (parentId: string) => void;
}) {
  const resolveComment = useResolveCardComment();

  return (
    <div className={cn("rounded-lg border p-3", comment.resolved ? "border-green-200 bg-green-50" : "border-border bg-card")}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-primary/10 text-xs font-medium text-primary">
            {comment.user_name.charAt(0).toUpperCase()}
          </div>
          <div>
            <span className="text-sm font-medium">{comment.user_name}</span>
            <span className="ml-2 text-xs text-muted-foreground">
              {new Date(comment.created_at).toLocaleDateString()}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-1">
          {!comment.parent_comment_id && (
            <button
              onClick={() => resolveComment.mutate({ cardId, commentId: comment.id })}
              className={cn(
                "rounded p-1 text-xs transition-colors hover:bg-muted",
                comment.resolved ? "text-green-600" : "text-muted-foreground"
              )}
              title={comment.resolved ? "Unresolve" : "Resolve"}
            >
              {comment.resolved ? <CheckCheck className="h-4 w-4" /> : <Check className="h-4 w-4" />}
            </button>
          )}
          <button
            onClick={() => onReply(comment.id)}
            className="rounded p-1 text-xs text-muted-foreground transition-colors hover:bg-muted"
            title="Reply"
          >
            <Reply className="h-4 w-4" />
          </button>
        </div>
      </div>
      <p className="mt-2 text-sm text-foreground">{comment.content}</p>

      {/* Threaded replies */}
      {comment.replies && comment.replies.length > 0 && (
        <div className="mt-3 space-y-2 border-l-2 border-muted pl-3">
          {comment.replies.map((reply) => (
            <CommentItem key={reply.id} comment={reply} cardId={cardId} onReply={onReply} />
          ))}
        </div>
      )}
    </div>
  );
}

export function CommentsPanel({ cardId }: CommentsPanelProps) {
  const { data: comments, isLoading } = useCardComments(cardId);
  const addComment = useAddCardComment();
  const [newComment, setNewComment] = useState("");
  const [replyingTo, setReplyingTo] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newComment.trim()) return;

    addComment.mutate(
      {
        id: cardId,
        comment: {
          content: newComment.trim(),
          parent_comment_id: replyingTo ?? undefined,
        },
      },
      {
        onSuccess: () => {
          setNewComment("");
          setReplyingTo(null);
        },
      }
    );
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-2 border-b px-4 py-3">
        <MessageSquare className="h-5 w-5 text-muted-foreground" />
        <h3 className="text-sm font-semibold">Comments</h3>
        <span className="text-xs text-muted-foreground">({comments?.length ?? 0})</span>
      </div>

      {/* Comments list */}
      <div className="flex-1 space-y-3 overflow-auto p-4">
        {comments && comments.length > 0 ? (
          comments.map((comment) => (
            <CommentItem key={comment.id} comment={comment} cardId={cardId} onReply={setReplyingTo} />
          ))
        ) : (
          <p className="py-8 text-center text-sm text-muted-foreground">No comments yet</p>
        )}
      </div>

      {/* New comment form */}
      <form onSubmit={handleSubmit} className="border-t p-4">
        {replyingTo && (
          <div className="mb-2 flex items-center gap-2 text-xs text-muted-foreground">
            <Reply className="h-3 w-3" />
            <span>Replying to comment</span>
            <button type="button" onClick={() => setReplyingTo(null)} className="text-primary hover:underline">
              Cancel
            </button>
          </div>
        )}
        <div className="flex gap-2">
          <input
            type="text"
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            placeholder={replyingTo ? "Write a reply..." : "Add a comment..."}
            className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          />
          <button
            type="submit"
            disabled={!newComment.trim() || addComment.isPending}
            className="inline-flex items-center justify-center rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </form>
    </div>
  );
}

