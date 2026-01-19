package com.celec.ipam;

import javax.ws.rs.GET;
import javax.ws.rs.Path;
import javax.ws.rs.Produces;
import javax.ws.rs.core.MediaType;

@Path("/status")
public class HealthCheck {

    @GET
    @Produces(MediaType.APPLICATION_JSON)
    public String checkStatus() {
        return "{\"status\": \"Servidor WildFly Operativo para QA\", \"version\": \"1.0\"}";
    }
}