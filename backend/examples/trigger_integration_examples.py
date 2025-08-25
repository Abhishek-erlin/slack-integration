"""
Integration examples showing how to use the Notification Trigger Service
in existing services like audit services, AI visibility, and competitor analysis.
"""
from uuid import UUID
from typing import Dict, Any, Optional
from services.trigger_service import NotificationTriggerService
from services.notification_service import NotificationService
from models.notification_models import NotificationType


class AuditServiceIntegrationExample:
    """Example of integrating trigger service with audit services."""
    
    def __init__(self, trigger_service: NotificationTriggerService):
        self.trigger_service = trigger_service
    
    async def complete_site_level_audit(
        self, 
        website_id: UUID, 
        user_id: UUID, 
        audit_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Example of how to integrate trigger service in audit completion.
        
        This shows the pattern for the site_level_check_service.py mentioned in memories.
        """
        try:
            # Existing audit logic would go here...
            # audit_result = await self._perform_audit(website_id)
            # saved_result = await self.audit_repository.save_audit_result(...)
            
            # Prepare context for notification
            context = {
                "audit_type": "site-level",
                "website_name": audit_results.get("website_url", "your website"),
                "score": audit_results.get("score", 0),
                "issues_count": len(audit_results.get("issues", [])),
                "audit_id": str(audit_results.get("id")),
                "completion_time": audit_results.get("completed_at")
            }
            
            # Trigger notification automatically
            trigger_result = await self.trigger_service.handle_event_trigger(
                user_id=user_id,
                website_id=website_id,
                event_type=NotificationType.AUDIT_COMPLETE,
                context=context
            )
            
            # Log the trigger result
            if trigger_result.success:
                print(f"Audit completion notification sent: {trigger_result.notification_id}")
            else:
                print(f"Failed to send audit completion notification: {trigger_result.message}")
            
            return audit_results
            
        except Exception as e:
            print(f"Error in audit completion with notification: {e}")
            return audit_results
    
    async def start_audit_notification(
        self, 
        website_id: UUID, 
        user_id: UUID, 
        audit_type: str,
        website_url: str
    ):
        """Example of notifying when audit starts - now using system alert."""
        context = {
            "alert_message": f"Your {audit_type} audit for {website_url} has started and will be completed shortly.",
            "audit_type": audit_type,
            "website_name": website_url,
            "estimated_duration": "5-10 minutes"
        }
        
        await self.trigger_service.handle_event_trigger(
            user_id=user_id,
            website_id=website_id,
            event_type=NotificationType.SYSTEM_ALERT,
            context=context
        )


class AIVisibilityServiceIntegrationExample:
    """Example of integrating trigger service with AI visibility updates."""
    
    def __init__(self, trigger_service: NotificationTriggerService):
        self.trigger_service = trigger_service
    
    async def update_ai_visibility_data(
        self, 
        website_id: UUID, 
        user_id: UUID, 
        visibility_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Example of AI visibility update integration."""
        try:
            # Existing AI visibility logic would go here...
            # visibility_results = await self._process_ai_visibility(website_id)
            # saved_data = await self.ai_repository.save_visibility_data(...)
            
            # Prepare context for notification
            context = {
                "website_name": visibility_data.get("website_url", "your website"),
                "visibility_score": visibility_data.get("visibility_score", 0),
                "insights_count": len(visibility_data.get("insights", [])),
                "improvement_suggestions": visibility_data.get("suggestions_count", 0),
                "data_id": str(visibility_data.get("id"))
            }
            
            # Use AI_VISIBILITY event type for AI visibility updates
            trigger_result = await self.trigger_service.handle_event_trigger(
                user_id=user_id,
                website_id=website_id,
                event_type=NotificationType.AI_VISIBILITY,
                context=context
            )
            
            return visibility_data
            
        except Exception as e:
            print(f"Error in AI visibility update with notification: {e}")
            return visibility_data


class CompetitorAnalysisServiceIntegrationExample:
    """Example of integrating trigger service with competitor analysis."""
    
    def __init__(self, trigger_service: NotificationTriggerService):
        self.trigger_service = trigger_service
    
    async def complete_competitor_analysis(
        self, 
        website_id: UUID, 
        user_id: UUID, 
        analysis_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Example of competitor analysis completion integration."""
        try:
            # Existing competitor analysis logic would go here...
            # analysis_results = await self._analyze_competitors(website_id, competitors)
            # saved_results = await self.competitor_repository.save_analysis_results(...)
            
            # Prepare context for notification
            competitors = analysis_results.get("competitors", [])
            context = {
                "website_name": analysis_results.get("website_url", "your website"),
                "competitor_count": len(competitors),
                "analysis_id": str(analysis_results.get("id")),
                "top_competitor": competitors[0].get("name", "") if competitors else "",
                "competitive_score": analysis_results.get("competitive_score", 0)
            }
            
            # Use COMPETITOR_ANALYSIS for competitor analysis completion
            trigger_result = await self.trigger_service.handle_event_trigger(
                user_id=user_id,
                website_id=website_id,
                event_type=NotificationType.COMPETITOR_ANALYSIS,
                context=context
            )
            
            return analysis_results
            
        except Exception as e:
            print(f"Error in competitor analysis with notification: {e}")
            return analysis_results


class SystemAlertIntegrationExample:
    """Example of integrating trigger service for system alerts."""
    
    def __init__(self, trigger_service: NotificationTriggerService):
        self.trigger_service = trigger_service
    
    async def send_maintenance_alert(
        self, 
        user_ids: list[UUID], 
        maintenance_details: Dict[str, Any]
    ):
        """Example of sending system maintenance alerts to multiple users."""
        context = {
            "alert_message": f"Scheduled maintenance: {maintenance_details.get('description', 'System maintenance')} "
                           f"on {maintenance_details.get('date')} at {maintenance_details.get('time')}. "
                           f"Expected duration: {maintenance_details.get('duration', 'TBD')}.",
            "maintenance_type": maintenance_details.get("type", "general"),
            "scheduled_time": maintenance_details.get("scheduled_time"),
            "affected_services": maintenance_details.get("affected_services", [])
        }
        
        # Send to all users (use a dummy website_id for system alerts)
        dummy_website_id = UUID("00000000-0000-0000-0000-000000000000")
        
        for user_id in user_ids:
            await self.trigger_service.handle_event_trigger(
                user_id=user_id,
                website_id=dummy_website_id,
                event_type=NotificationType.SYSTEM_ALERT,
                context=context
            )
    
    async def send_integration_status_alert(
        self, 
        user_id: UUID, 
        website_id: UUID, 
        integration_name: str, 
        status: str, 
        details: str = ""
    ):
        """Example of sending integration status alerts."""
        context = {
            "status_message": f"{integration_name} integration {status}. {details}".strip(),
            "integration_name": integration_name,
            "status": status,
            "timestamp": "now"
        }
        
        await self.trigger_service.handle_event_trigger(
            user_id=user_id,
            website_id=website_id,
            event_type=NotificationType.INTEGRATION_STATUS,
            context=context
        )


# Example of how to set up the trigger service in your existing services
def setup_trigger_service_integration():
    """
    Example of how to set up trigger service integration in your existing services.
    
    This would typically be done in your dependency injection setup.
    """
    # Create notification service (your existing service)
    notification_service = NotificationService()
    
    # Create trigger service
    trigger_service = NotificationTriggerService(notification_service)
    
    # Create service instances with trigger integration
    audit_service = AuditServiceIntegrationExample(trigger_service)
    ai_visibility_service = AIVisibilityServiceIntegrationExample(trigger_service)
    competitor_service = CompetitorAnalysisServiceIntegrationExample(trigger_service)
    system_alert_service = SystemAlertIntegrationExample(trigger_service)
    
    return {
        "audit_service": audit_service,
        "ai_visibility_service": ai_visibility_service,
        "competitor_service": competitor_service,
        "system_alert_service": system_alert_service,
        "trigger_service": trigger_service
    }


# Example usage in your existing service classes
"""
# In your existing site_level_check_service.py:

class SiteLevelCheckService:
    def __init__(self, audit_repository, trigger_service: NotificationTriggerService):
        self.audit_repository = audit_repository
        self.trigger_service = trigger_service
    
    async def check_site_level_parameters(self, website_id, user_id):
        # Your existing audit logic...
        audit_result = await self._perform_audit(website_id)
        
        # Save the audit result (your existing code)
        saved_result = await self.audit_repository.save_audit_result(
            website_id=website_id,
            audit_type="site_level",
            audit_data=audit_result,
            user_id=user_id
        )
        
        # NEW: Trigger notification
        await self.trigger_service.handle_event_trigger(
            user_id=user_id,
            website_id=website_id,
            event_type=NotificationType.AUDIT_COMPLETE,
            context={
                "audit_type": "site-level",
                "website_name": saved_result.get("website_url", "your website"),
                "score": saved_result.get("score", 0),
                "issues_count": len(saved_result.get("issues", [])),
                "audit_id": str(saved_result.get("id"))
            }
        )
        
        return saved_result
"""
