$(document).ready(function () {
    $('#tablaCancelaciones').DataTable({
        // CONFIGURACIÓN CLAVE: Colocamos botones (B) y buscador (f) en la misma línea
        dom: "<'row mb-3 align-items-center'<'col-md-6'B><'col-md-6 d-flex justify-content-end'f>>" +
             "<'row'<'col-sm-12'tr>>" +
             "<'row mt-3'<'col-md-5'i><'col-md-7 d-flex justify-content-end'p>>",

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

        language: {
            sSearch: "Buscar:",
            sLengthMenu: "Mostrar _MENU_ registros",
            sInfo: "Mostrando _START_ a _END_ de _TOTAL_ registros",
            sZeroRecords: "No se encontraron resultados",
            sEmptyTable: "No hay datos disponibles"
        },

        responsive: false,
        autoWidth: true,
        scrollX: false,
        scrollCollapse: false
    });
});