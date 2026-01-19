package com.celec.ipam.service;

import com.celec.ipam.model.UnidadNegocio;
import javax.ejb.Stateless;
import javax.persistence.EntityManager;
import javax.persistence.PersistenceContext;
import java.util.List;

@Stateless
public class UnidadService {

    // Aquí inyectamos el Persistence Unit "IPAM_PU" que definimos antes
    @PersistenceContext(unitName = "IPAM_PU")
    private EntityManager em;

    // Método para guardar o actualizar una unidad
    public void guardarUnidad(UnidadNegocio unidad) {
        if (unidad.getId() == null) {
            em.persist(unidad);
        } else {
            em.merge(unidad);
        }
    }

    // Método para obtener todas las unidades (Útil para el Dashboard)
    public List<UnidadNegocio> listarTodas() {
        return em.createQuery("SELECT u FROM UnidadNegocio u", UnidadNegocio.class)
                 .getResultList();
    }

    // Método para buscar una unidad por ID
    public UnidadNegocio buscarPorId(Long id) {
        return em.find(UnidadNegocio.class, id);
    }
}