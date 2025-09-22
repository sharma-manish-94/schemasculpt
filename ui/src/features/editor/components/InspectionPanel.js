import React, {useMemo} from "react";
import SwaggerUI from "swagger-ui-react";
import {useSpecStore} from "../../../store/specStore";

function LivePreview({endpoint, operationDetails}) {
    const minispec = useMemo(() => {
        // If we have tree-shaken operation details from the API, use that
        if (operationDetails) {
            return operationDetails;
        }
        // Fall back to building a minimal spec from the endpoint
        if (!endpoint) {
            return null;
        }
        return {
            openapi: '3.0.0', info: {
                title: 'Live Preview', version: '1.0.0',
            }, paths: {
                [endpoint.path]: {
                    [endpoint.method.toLowerCase()]: endpoint.details,
                },
            },
        };
    }, [endpoint, operationDetails]);
    if (!minispec) {
        return null;
    }
    return <SwaggerUI spec={minispec}/>;
}


function InspectionPanel() {
    const selectedNavItem = useSpecStore((state) => state.selectedNavItem);
    const selectedNavItemDetails = useSpecStore((state) => state.selectedNavItemDetails);
    const isNavItemLoading = useSpecStore((state) => state.isNavItemLoading);

    // content is determined by the application's state
    let content = null;
    if (selectedNavItem) {
        // Show the live preview if an item is selected
        if (isNavItemLoading) {
            content = <div className="panel-content-placeholder">Loading operation details...</div>;
        } else {
            content = <LivePreview endpoint={selectedNavItem} operationDetails={selectedNavItemDetails}/>;
        }
    } else {
        content = <div className = "panel-content-placeholder"> Select an item to see a preview</div>;
    }

    return (
        <div className="inspection-panel">
            <div className="panel-header">Inspector</div>
            <div className="panel-content">
                {content}
            </div>
        </div>
    )
}

export default InspectionPanel;