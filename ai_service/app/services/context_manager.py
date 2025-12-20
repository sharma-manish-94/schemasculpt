"""
Context Management Service for SchemaSculpt AI.
Provides conversation continuity, session management, and intelligent context caching.
"""

from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from ..core.config import settings
from ..core.logging import get_logger
from ..schemas.ai_schemas import AIRequest, AIResponse, ContextWindow


@dataclass
class ConversationTurn:
    """Represents a single conversation turn."""

    turn_id: str
    timestamp: datetime
    request: Dict[str, Any]  # Serialized AIRequest
    response: Dict[str, Any]  # Serialized AIResponse
    operation_type: str
    success: bool
    processing_time_ms: float
    tokens_used: int


@dataclass
class SessionMetrics:
    """Metrics for a conversation session."""

    total_turns: int
    total_tokens: int
    total_processing_time_ms: float
    success_rate: float
    common_operations: List[str]
    average_response_time_ms: float


class ContextManager:
    """
    Advanced context management for maintaining conversation continuity
    and learning from interaction patterns.
    """

    def __init__(self):
        self.logger = get_logger("context_manager")

        # Active conversations
        self._conversations: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=settings.cache_ttl)
        )

        # Session summaries for long-term context
        self._session_summaries: Dict[str, Dict[str, Any]] = {}

        # Pattern recognition
        self._operation_patterns: Dict[str, List[str]] = defaultdict(list)
        self._success_patterns: Dict[str, int] = defaultdict(int)
        self._failure_patterns: Dict[str, int] = defaultdict(int)

        # Performance tracking
        self._performance_metrics: Dict[str, SessionMetrics] = {}

    def create_session(self, user_id: Optional[str] = None) -> str:
        """Create a new conversation session."""
        session_id = str(uuid4())

        self.logger.info(
            f"Created new session: {session_id}",
            extra={"session_id": session_id, "user_id": user_id},
        )

        # Initialize session metrics
        self._performance_metrics[session_id] = SessionMetrics(
            total_turns=0,
            total_tokens=0,
            total_processing_time_ms=0,
            success_rate=0.0,
            common_operations=[],
            average_response_time_ms=0.0,
        )

        return session_id

    def add_conversation_turn(
        self,
        session_id: str,
        request: AIRequest,
        response: AIResponse,
        success: bool = True,
    ) -> None:
        """Add a conversation turn to the session context."""
        turn = ConversationTurn(
            turn_id=str(uuid4()),
            timestamp=datetime.utcnow(),
            request=self._serialize_request(request),
            response=self._serialize_response(response),
            operation_type=request.operation_type.value,
            success=success,
            processing_time_ms=response.performance.processing_time_ms,
            tokens_used=response.performance.token_count,
        )

        # Add to conversation history
        self._conversations[session_id].append(turn)

        # Update metrics
        self._update_session_metrics(session_id, turn)

        # Learn patterns
        self._learn_from_turn(turn)

        self.logger.info(
            f"Added conversation turn to session {session_id}",
            extra={
                "turn_id": turn.turn_id,
                "operation_type": turn.operation_type,
                "success": success,
                "tokens": turn.tokens_used,
            },
        )

    def get_context_for_request(
        self, session_id: str, current_request: AIRequest
    ) -> ContextWindow:
        """Get intelligent context for the current request."""
        if session_id not in self._conversations:
            # Return default context for new sessions
            return ContextWindow(
                conversation_id=UUID(session_id) if session_id else uuid4(),
                previous_operations=[],
                context_size=(
                    current_request.context.context_size
                    if current_request.context
                    else 10
                ),
                preserve_context=True,
            )

        conversation = self._conversations[session_id]
        context_size = (
            current_request.context.context_size if current_request.context else 10
        )

        # Get relevant previous operations
        previous_operations = self._extract_relevant_operations(
            conversation, current_request, context_size
        )

        return ContextWindow(
            conversation_id=UUID(session_id),
            previous_operations=previous_operations,
            context_size=context_size,
            preserve_context=True,
        )

    def _extract_relevant_operations(
        self, conversation: deque, current_request: AIRequest, context_size: int
    ) -> List[str]:
        """Extract the most relevant previous operations for context."""
        # Simple strategy: return recent operations of similar type
        relevant_ops = []

        # First, look for operations of the same type
        for turn in reversed(conversation):
            if len(relevant_ops) >= context_size:
                break

            if turn.operation_type == current_request.operation_type.value:
                relevant_ops.append(f"{turn.operation_type}: {turn.success}")

        # Fill remaining slots with recent operations
        for turn in reversed(conversation):
            if len(relevant_ops) >= context_size:
                break

            op_desc = f"{turn.operation_type}: {turn.success}"
            if op_desc not in relevant_ops:
                relevant_ops.append(op_desc)

        return relevant_ops[:context_size]

    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get a summary of the session for context."""
        if session_id not in self._conversations:
            return {"error": "Session not found"}

        conversation = self._conversations[session_id]
        self._performance_metrics.get(session_id)

        # Analyze conversation patterns
        operation_counts = defaultdict(int)
        success_count = 0
        total_tokens = 0
        total_time = 0

        for turn in conversation:
            operation_counts[turn.operation_type] += 1
            if turn.success:
                success_count += 1
            total_tokens += turn.tokens_used
            total_time += turn.processing_time_ms

        total_turns = len(conversation)

        return {
            "session_id": session_id,
            "total_turns": total_turns,
            "success_rate": success_count / total_turns if total_turns > 0 else 0,
            "total_tokens": total_tokens,
            "total_processing_time_ms": total_time,
            "average_time_per_turn_ms": (
                total_time / total_turns if total_turns > 0 else 0
            ),
            "operation_distribution": dict(operation_counts),
            "most_common_operation": (
                max(operation_counts, key=operation_counts.get)
                if operation_counts
                else None
            ),
            "session_duration_minutes": self._calculate_session_duration(conversation),
            "conversation_flow": self._analyze_conversation_flow(conversation),
        }

    def _calculate_session_duration(self, conversation: deque) -> float:
        """Calculate session duration in minutes."""
        if len(conversation) < 2:
            return 0

        start_time = conversation[0].timestamp
        end_time = conversation[-1].timestamp
        duration = end_time - start_time

        return duration.total_seconds() / 60

    def _analyze_conversation_flow(self, conversation: deque) -> List[str]:
        """Analyze the flow of operations in the conversation."""
        flow = []
        for turn in conversation:
            status = "✓" if turn.success else "✗"
            flow.append(f"{turn.operation_type}{status}")

        return flow

    def get_intelligent_suggestions(
        self, session_id: str, current_request: AIRequest
    ) -> List[str]:
        """Get intelligent suggestions based on session context and patterns."""
        suggestions = []

        if session_id in self._conversations:
            conversation = self._conversations[session_id]

            # Analyze recent failures for suggestions
            recent_failures = [
                turn
                for turn in list(conversation)[-5:]  # Last 5 turns
                if not turn.success
            ]

            if recent_failures:
                suggestions.append(
                    "Consider enabling auto_fix for better error recovery"
                )

            # Suggest based on operation patterns
            if current_request.operation_type.value in self._operation_patterns:
                common_next_ops = self._operation_patterns[
                    current_request.operation_type.value
                ][-3:]
                if common_next_ops:
                    suggestions.append(
                        f"Users often follow this with: {', '.join(set(common_next_ops))}"
                    )

            # Performance suggestions
            if len(conversation) > 0:
                avg_tokens = sum(turn.tokens_used for turn in conversation) / len(
                    conversation
                )
                if avg_tokens > 2000:
                    suggestions.append(
                        "Consider using streaming for better responsiveness"
                    )

        return suggestions

    def _serialize_request(self, request: AIRequest) -> Dict[str, Any]:
        """Serialize AIRequest for storage."""
        return {
            "operation_type": request.operation_type.value,
            "prompt": request.prompt[:200],  # Truncate for storage
            "streaming": request.streaming.value,
            "validate_output": request.validate_output,
            "auto_fix": request.auto_fix,
            "has_patches": bool(request.json_patches),
            "target_paths": request.target_paths,
            "user_id": request.user_id,
            "session_id": str(request.session_id) if request.session_id else None,
        }

    def _serialize_response(self, response: AIResponse) -> Dict[str, Any]:
        """Serialize AIResponse for storage."""
        return {
            "operation_type": response.operation_type.value,
            "confidence_score": response.confidence_score,
            "changes_summary": response.changes_summary[:200],  # Truncate
            "validation_valid": response.validation.is_valid,
            "validation_errors": len(response.validation.errors),
            "modified_paths": response.modified_paths,
            "processing_time_ms": response.performance.processing_time_ms,
            "token_count": response.performance.token_count,
            "model_used": response.performance.model_used,
        }

    def _update_session_metrics(self, session_id: str, turn: ConversationTurn) -> None:
        """Update session metrics with new turn data."""
        metrics = self._performance_metrics[session_id]

        metrics.total_turns += 1
        metrics.total_tokens += turn.tokens_used
        metrics.total_processing_time_ms += turn.processing_time_ms

        # Update success rate
        conversation = self._conversations[session_id]
        successful_turns = sum(1 for t in conversation if t.success)
        metrics.success_rate = successful_turns / len(conversation)

        # Update average response time
        metrics.average_response_time_ms = (
            metrics.total_processing_time_ms / metrics.total_turns
        )

        # Update common operations
        operation_counts = defaultdict(int)
        for t in conversation:
            operation_counts[t.operation_type] += 1

        metrics.common_operations = sorted(
            operation_counts.items(), key=lambda x: x[1], reverse=True
        )[
            :3
        ]  # Top 3 operations

    def _learn_from_turn(self, turn: ConversationTurn) -> None:
        """Learn patterns from conversation turns."""
        # Track operation sequences
        session_conversation = None
        for conv in self._conversations.values():
            if any(t.turn_id == turn.turn_id for t in conv):
                session_conversation = conv
                break

        if session_conversation and len(session_conversation) > 1:
            # Previous operation
            prev_turn = list(session_conversation)[-2]
            self._operation_patterns[prev_turn.operation_type].append(
                turn.operation_type
            )

        # Track success/failure patterns
        pattern_key = f"{turn.operation_type}_{turn.success}"
        if turn.success:
            self._success_patterns[pattern_key] += 1
        else:
            self._failure_patterns[pattern_key] += 1

    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions to free memory."""
        expired_sessions = []
        cutoff_time = datetime.utcnow() - timedelta(hours=24)  # 24 hour expiry

        for session_id, conversation in self._conversations.items():
            if conversation and conversation[-1].timestamp < cutoff_time:
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            del self._conversations[session_id]
            if session_id in self._performance_metrics:
                del self._performance_metrics[session_id]

        self.logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
        return len(expired_sessions)

    def get_global_patterns(self) -> Dict[str, Any]:
        """Get global patterns across all sessions."""
        return {
            "total_active_sessions": len(self._conversations),
            "total_conversations": sum(
                len(conv) for conv in self._conversations.values()
            ),
            "success_patterns": dict(self._success_patterns),
            "failure_patterns": dict(self._failure_patterns),
            "operation_sequences": {
                op: sequences[-10:]  # Last 10 sequences per operation
                for op, sequences in self._operation_patterns.items()
            },
        }

    def export_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Export session data for analysis or backup."""
        if session_id not in self._conversations:
            return None

        conversation = self._conversations[session_id]
        metrics = self._performance_metrics.get(session_id)

        return {
            "session_id": session_id,
            "conversation_turns": [asdict(turn) for turn in conversation],
            "metrics": asdict(metrics) if metrics else None,
            "summary": self.get_session_summary(session_id),
            "export_timestamp": datetime.utcnow().isoformat(),
        }

    def get_context_statistics(self) -> Dict[str, Any]:
        """Get statistics about context management performance."""
        total_turns = sum(len(conv) for conv in self._conversations.values())
        total_sessions = len(self._conversations)

        if total_sessions == 0:
            return {"message": "No active sessions"}

        avg_turns_per_session = total_turns / total_sessions
        avg_success_rate = sum(
            metrics.success_rate for metrics in self._performance_metrics.values()
        ) / len(self._performance_metrics)

        return {
            "total_active_sessions": total_sessions,
            "total_conversation_turns": total_turns,
            "average_turns_per_session": avg_turns_per_session,
            "average_success_rate": avg_success_rate,
            "memory_usage_mb": self._estimate_memory_usage(),
            "pattern_learning": {
                "operation_patterns": len(self._operation_patterns),
                "success_patterns": len(self._success_patterns),
                "failure_patterns": len(self._failure_patterns),
            },
        }

    def _estimate_memory_usage(self) -> float:
        """Rough estimate of memory usage in MB."""
        import sys

        total_size = 0

        # Estimate conversation size
        for conversation in self._conversations.values():
            total_size += sys.getsizeof(conversation)
            for turn in conversation:
                total_size += sys.getsizeof(turn)

        # Estimate metrics size
        for metrics in self._performance_metrics.values():
            total_size += sys.getsizeof(metrics)

        # Estimate patterns size
        total_size += sys.getsizeof(self._operation_patterns)
        total_size += sys.getsizeof(self._success_patterns)
        total_size += sys.getsizeof(self._failure_patterns)

        return total_size / (1024 * 1024)  # Convert to MB
