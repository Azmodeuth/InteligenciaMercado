"""
================================================================================
QUERIES GRAPHQL PARA REVOLICO - VERSIÓN V2.5 (APOLLO COMPATIBLE)
================================================================================
"""
QUERY_BUSQUEDA = """
query AdsSearch($category: ID, $subcategory: ID, $contains: String, $price: BasePriceFilterInput, $sort: [adsPerPageSort], $hasImage: Boolean, $categorySlug: String, $subcategorySlug: String, $page: Int, $provinceSlug: String, $municipalitySlug: String, $pageLength: Int) {
  adsPerPage(
    category: $category, subcategory: $subcategory, contains: $contains, price: $price, hasImage: $hasImage, sort: $sort,
    categorySlug: $categorySlug, subcategorySlug: $subcategorySlug, page: $page, provinceSlug: $provinceSlug,
    municipalitySlug: $municipalitySlug, pageLength: $pageLength
  ) {
    pageInfo { hasNextPage __typename }
    edges {
      node {
        id title price currency permalink description
        phoneInfo { firstPhone { number __typename } __typename }
        __typename
      }
      __typename
    }
    __typename
  }
}
"""

QUERY_DETALLE_ANUNCIO = """
query AdDetail($id: ID!) {
  ad(id: $id) {
    id title price currency permalink body description
    phoneInfo {
      firstPhone { number type __typename }
      __typename
    }
    __typename
  }
}
"""