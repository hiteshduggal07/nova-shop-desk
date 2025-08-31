import React, { useState, useMemo } from 'react';
import { Filter, X } from 'lucide-react';
import { mockProducts, categories } from '@/data/products';
import { useStore } from '@/contexts/StoreContext';
import { ProductCard } from '@/components/ProductCard';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Slider } from '@/components/ui/slider';
import { Checkbox } from '@/components/ui/checkbox';

export default function Products() {
  const { state, dispatch } = useStore();
  const [showMobileFilters, setShowMobileFilters] = useState(false);

  // Initialize products data
  React.useEffect(() => {
    if (state.products.length === 0) {
      // In a real app, you'd dispatch SET_PRODUCTS action
      // For now, we'll work with the mockProducts directly
    }
  }, [state.products]);

  // Enhanced search function that handles singular/plural and similar word forms
  const searchProducts = (query: string, products: typeof mockProducts) => {
    if (!query.trim()) return products;
    
    const searchTerm = query.toLowerCase().trim();
    const searchWords = searchTerm.split(/\s+/);
    
    return products.filter(product => {
      const productText = [
        product.name.toLowerCase(),
        product.category.toLowerCase(),
        product.description.toLowerCase(),
        ...product.features.map(f => f.toLowerCase())
      ].join(' ');
      
      // Check if any search word matches the product
      return searchWords.some(word => {
        // Exact match
        if (productText.includes(word)) return true;
        
        // Handle singular/plural variations
        const singularForms = getSingularForms(word);
        const pluralForms = getPluralForms(word);
        
        // Check singular forms
        if (singularForms.some(form => productText.includes(form))) return true;
        
        // Check plural forms  
        if (pluralForms.some(form => productText.includes(form))) return true;
        
        // Handle common abbreviations and variations
        const variations = getWordVariations(word);
        if (variations.some(variation => productText.includes(variation))) return true;
        
        return false;
      });
    });
  };

  // Helper function to get singular forms of a word
  const getSingularForms = (word: string): string[] => {
    const forms = [word];
    
    // Common plural to singular rules
    if (word.endsWith('ies')) {
      forms.push(word.slice(0, -3) + 'y'); // categories -> category
    }
    if (word.endsWith('s')) {
      forms.push(word.slice(0, -1)); // shirts -> shirt
    }
    if (word.endsWith('es')) {
      forms.push(word.slice(0, -2)); // shoes -> shoe
    }
    
    return forms;
  };

  // Helper function to get plural forms of a word
  const getPluralForms = (word: string): string[] => {
    const forms = [word];
    
    // Common singular to plural rules
    if (word.endsWith('y')) {
      forms.push(word.slice(0, -1) + 'ies'); // category -> categories
    }
    if (!word.endsWith('s')) {
      forms.push(word + 's'); // shirt -> shirts
    }
    if (word.endsWith('e')) {
      forms.push(word + 's'); // shoe -> shoes
    }
    
    return forms;
  };

  // Helper function to get word variations and abbreviations
  const getWordVariations = (word: string): string[] => {
    const variations = [word];
    
    // Common abbreviations
    if (word === 'tv' || word === 'television') {
      variations.push('tv', 'television');
    }
    if (word === 'phone' || word === 'smartphone') {
      variations.push('phone', 'smartphone', 'mobile');
    }
    if (word === 'laptop' || word === 'computer') {
      variations.push('laptop', 'computer', 'pc');
    }
    if (word === 'headphones' || word === 'earphones') {
      variations.push('headphones', 'earphones', 'earbuds');
    }
    
    // Handle common word endings
    if (word.endsWith('ing')) {
      variations.push(word.slice(0, -3)); // running -> run
    }
    
    return variations;
  };

  // Filter products based on current filters
  const filteredProducts = useMemo(() => {
    let filtered = mockProducts;

    // Enhanced search filter
    if (state.searchQuery) {
      filtered = searchProducts(state.searchQuery, filtered);
    }

    // Category filter
    if (state.selectedCategory && state.selectedCategory !== 'All') {
      filtered = filtered.filter(product => product.category === state.selectedCategory);
    }

    // Price range filter
    filtered = filtered.filter(product => 
      product.price >= state.priceRange[0] && product.price <= state.priceRange[1]
    );

    // Rating filter
    filtered = filtered.filter(product => product.rating >= state.minRating);

    return filtered;
  }, [state.searchQuery, state.selectedCategory, state.priceRange, state.minRating]);

  const handleCategoryChange = (category: string) => {
    dispatch({ type: 'SET_CATEGORY', payload: category });
  };

  const handlePriceRangeChange = (value: number[]) => {
    dispatch({ type: 'SET_PRICE_RANGE', payload: [value[0], value[1]] });
  };

  const handleRatingChange = (rating: number) => {
    dispatch({ type: 'SET_MIN_RATING', payload: rating });
  };

  const clearFilters = () => {
    dispatch({ type: 'SET_CATEGORY', payload: 'All' });
    dispatch({ type: 'SET_PRICE_RANGE', payload: [0, 1000] });
    dispatch({ type: 'SET_MIN_RATING', payload: 0 });
    dispatch({ type: 'SET_SEARCH_QUERY', payload: '' });
  };

  const FilterSidebar = () => (
    <div className="space-y-6">
      {/* Clear Filters */}
      <div className="flex justify-between items-center">
        <h3 className="font-semibold text-lg">Filters</h3>
        <Button variant="ghost" size="sm" onClick={clearFilters}>
          Clear All
        </Button>
      </div>

      {/* Categories */}
      <div className="filter-section">
        <h4 className="font-medium mb-3">Categories</h4>
        <div className="space-y-2">
          {categories.map((category) => (
            <div key={category} className="flex items-center space-x-2">
              <Checkbox
                id={category}
                checked={state.selectedCategory === category}
                onCheckedChange={() => handleCategoryChange(category)}
              />
              <label htmlFor={category} className="text-sm cursor-pointer">
                {category}
              </label>
            </div>
          ))}
        </div>
      </div>

      {/* Price Range */}
      <div className="filter-section">
        <h4 className="font-medium mb-3">Price Range</h4>
        <div className="px-2">
          <Slider
            value={state.priceRange}
            onValueChange={handlePriceRangeChange}
            max={1000}
            min={0}
            step={10}
            className="mb-4"
          />
          <div className="flex justify-between text-sm text-muted-foreground">
            <span>${state.priceRange[0]}</span>
            <span>${state.priceRange[1]}</span>
          </div>
        </div>
      </div>

      {/* Rating */}
      <div className="filter-section">
        <h4 className="font-medium mb-3">Minimum Rating</h4>
        <div className="space-y-2">
          {[4, 3, 2, 1, 0].map((rating) => (
            <div key={rating} className="flex items-center space-x-2">
              <Checkbox
                id={`rating-${rating}`}
                checked={state.minRating === rating}
                onCheckedChange={() => handleRatingChange(rating)}
              />
              <label htmlFor={`rating-${rating}`} className="text-sm cursor-pointer">
                {rating === 0 ? 'All Ratings' : `${rating}+ Stars`}
              </label>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-heading font-bold mb-2">All Products</h1>
          <p className="text-muted-foreground">
            Showing {filteredProducts.length} of {mockProducts.length} products
          </p>
        </div>
        
        {/* Mobile Filter Button */}
        <Button
          variant="outline"
          className="lg:hidden"
          onClick={() => setShowMobileFilters(true)}
        >
          <Filter className="w-4 h-4 mr-2" />
          Filters
        </Button>
      </div>

      {/* Active Filters */}
      {(state.selectedCategory !== 'All' || state.minRating > 0 || state.searchQuery) && (
        <div className="flex flex-wrap gap-2 mb-6">
          {state.searchQuery && (
            <Badge variant="secondary" className="flex items-center gap-1">
              Search: "{state.searchQuery}"
              <X 
                className="w-3 h-3 cursor-pointer" 
                onClick={() => dispatch({ type: 'SET_SEARCH_QUERY', payload: '' })}
              />
            </Badge>
          )}
          {state.selectedCategory !== 'All' && (
            <Badge variant="secondary" className="flex items-center gap-1">
              {state.selectedCategory}
              <X 
                className="w-3 h-3 cursor-pointer" 
                onClick={() => dispatch({ type: 'SET_CATEGORY', payload: 'All' })}
              />
            </Badge>
          )}
          {state.minRating > 0 && (
            <Badge variant="secondary" className="flex items-center gap-1">
              {state.minRating}+ Stars
              <X 
                className="w-3 h-3 cursor-pointer" 
                onClick={() => dispatch({ type: 'SET_MIN_RATING', payload: 0 })}
              />
            </Badge>
          )}
        </div>
      )}

      <div className="flex gap-8">
        {/* Desktop Filters Sidebar */}
        <div className="hidden lg:block w-64 flex-shrink-0">
          <FilterSidebar />
        </div>

        {/* Products Grid */}
        <div className="flex-1">
          {/* Search Results Info */}
          {state.searchQuery && (
            <div className="mb-6 p-4 bg-muted/30 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-medium">
                  Search Results for "{state.searchQuery}"
                </h3>
                <Badge variant="secondary">
                  {filteredProducts.length} product{filteredProducts.length !== 1 ? 's' : ''} found
                </Badge>
              </div>
              <p className="text-sm text-muted-foreground">
                💡 Try searching for similar terms: "shirt" vs "shirts", "shoe" vs "shoes", or "phone" vs "smartphone"
              </p>
            </div>
          )}

          {filteredProducts.length > 0 ? (
            <div className="product-grid">
              {filteredProducts.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
          ) : (
            <div className="text-center py-16">
              <p className="text-muted-foreground text-lg mb-4">
                No products found matching your criteria.
              </p>
              {state.searchQuery && (
                <div className="mb-4 p-4 bg-muted/30 rounded-lg max-w-md mx-auto">
                  <p className="text-sm text-muted-foreground mb-2">
                    💡 Search tips:
                  </p>
                  <ul className="text-sm text-muted-foreground text-left space-y-1">
                    <li>• Try singular/plural variations (e.g., "shirt" vs "shirts")</li>
                    <li>• Use common abbreviations (e.g., "tv" or "phone")</li>
                    <li>• Search by category or product type</li>
                  </ul>
                </div>
              )}
              <Button onClick={clearFilters}>Clear Filters</Button>
            </div>
          )}
        </div>
      </div>

      {/* Mobile Filter Overlay */}
      {showMobileFilters && (
        <div className="fixed inset-0 bg-black/50 z-50 lg:hidden">
          <div className="absolute right-0 top-0 h-full w-80 bg-background p-6 overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h3 className="font-semibold text-lg">Filters</h3>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowMobileFilters(false)}
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
            <FilterSidebar />
            <div className="mt-6 pt-6 border-t">
              <Button 
                className="w-full"
                onClick={() => setShowMobileFilters(false)}
              >
                Show {filteredProducts.length} Products
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}