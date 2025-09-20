import React from "react";
import {useMemo} from "react";
import SwaggerUI from "swagger-ui-react";
import {useResponseStore} from "../../../store/responseStore";
import {useRequestStore} from "../../../store/requestStore";

function LivePreview({endpoint}) {
    const minispec = useMemo(() => {
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
    }, [endpoint]);
    if (!minispec) {
        return null;
    }
    return <SwaggerUI spec={minispec}/>;
}

function ResponseViewer() {
    const {apiResponse, isApiRequestLoading} = useResponseStore();
    if (isApiRequestLoading) {
        return <p className="loading-text">Waiting for response...</p>;
    }
    if (!apiResponse) {
        return <p className="no-errors">Response will be displayed here.</p>;
    }
    return (<pre className={apiResponse.success ? 'response-success' : 'response-error'}>
            {JSON.stringify(apiResponse.data || apiResponse.error, null, 2)}
        </pre>);
}

function InspectionPanel() {
    const selectedNavItem = useRequestStore((state) => state.selectedNavItem);
    const apiResponse = useResponseStore((state) => state.apiResponse);

    // content is determined by the application's state
    let content = null;
    if (apiResponse) {
        // Priority 1: show API Response
        content = <ResponseViewer/>;
    } else if (selectedNavItem) {
        // Priority 2: if an item is selected, show the live preview
        content = <LivePreview endpoint={selectedNavItem}/>;
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