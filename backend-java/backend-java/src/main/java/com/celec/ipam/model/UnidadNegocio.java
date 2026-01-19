package com.celec.ipam.model;

import javax.persistence.*;
import java.io.Serializable;

@Entity
@Table(name = "unidades_negocio")
public class UnidadNegocio implements Serializable {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 100)
    private String nombre;

    @Column(name = "segmento_base", nullable = false, unique = true, length = 50)
    private String segmentoBase;

    // Constructores
    public UnidadNegocio() {}

    // Getters y Setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getNombre() { return nombre; }
    public void setNombre(String nombre) { this.nombre = nombre; }

    public String getSegmentoBase() { return segmentoBase; }
    public void setSegmentoBase(String segmentoBase) { this.segmentoBase = segmentoBase; }
}