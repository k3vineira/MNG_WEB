$(document).ready(function() {
    $('#tablaTarifas').DataTable({
       // 1. ESTRUCTURA VISUAL: Mantiene botones y buscador alineados en la misma fila
        dom: "<'row mb-3 align-items-center'<'col-md-6'B><'col-md-6 d-flex justify-content-end'f>>" +
             "<'row'<'col-sm-12'tr>>" +
             "<'row mt-3'<'col-md-5'i><'col-md-7 d-flex justify-content-end'p>>",

        // 2. BOTONES DE EXPORTACIÓN
        buttons: [
            {
                extend: 'excelHtml5',
                text: 'Excel',
                className: 'btn btn-success btn-sm mx-1 rounded'
            },
            {
                extend: 'pdfHtml5',
                text: 'PDF',
                className: 'btn btn-danger btn-sm mx-1 rounded'
            },
            {
                extend: 'print',
                text: 'Imprimir',
                className: 'btn btn-info btn-sm text-white mx-1 rounded'
            }
        ],

        // 3. TRADUCCIÓN COMPLETA DE TU PROYECTO MONAGUA
        language: {
            sProcessing:     "Procesando...",
            sLengthMenu:     "Mostrar _MENU_ registros",
            sZeroRecords:    "No se encontraron resultados",
            sEmptyTable:     "Ningún dato disponible en esta tabla",
            sInfo:           "Mostrando registros del _START_ al _END_ de un total de _TOTAL_ registros",
            sInfoEmpty:      "Mostrando registros del 0 al 0 de un total de 0 registros",
            sInfoFiltered:   "(filtrado de un total de _MAX_ registros)",
            sInfoPostFix:    "",
            sSearch:         "Buscar:",
            sUrl:            "",
            sInfoThousands:  ",",
            sLoadingRecords: "Cargando...",
            oPaginate: {
                sFirst:    "Primero",
                sLast:     "Último",
                sNext:     "Siguiente",
                sPrevious: "Anterior"
            },
            oAria: {
                sSortAscending:  ": Activar para ordenar la columna de manera ascendente",
                sSortDescending: ": Activar para ordenar la columna de manera descendente"
            }
        },

        // 4. CONFIGURACIÓN DE AJUSTES Y RESPONSIVE
        responsive: false,
        autoWidth: true,
        scrollX: false,
        scrollCollapse: false
    });
});