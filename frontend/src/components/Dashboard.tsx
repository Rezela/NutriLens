import { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { ChartContainer } from '@/components/ui/chart';
import { PieChart, Pie, Cell } from 'recharts';
import { Flame, Beef, Wheat, Droplet, Plus, ChevronLeft, ChevronRight, Scan, Sparkles, Target } from 'lucide-react';
import { CameraCapture } from './CameraCapture';
import { BottomNavigation } from './BottomNavigation';
import { toast } from '@/hooks/use-toast';
import {
  analyzeMealImage,
  fetchDailyRecommendation,
  fetchDailyNutritionStats,
  fetchMealLogs,
  getStoredUserProfile,
  type DailyRecommendationResponse,
  type DailyNutritionStats,
  type MealLogResponse,
  type StoredUserProfile,
} from '@/lib/nutrilens';

const formatApiDate = (date: Date) => date.toISOString().split('T')[0];

const formatMealTime = (value: string) => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
};

const formatGoalLabel = (value: string | null) => {
  if (!value) {
    return 'Daily guidance';
  }
  return value
    .split('-')
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(' ');
};

const getPriorityClasses = (priority: string) => {
  if (priority === 'high') {
    return 'bg-red-100 text-red-700';
  }
  if (priority === 'medium') {
    return 'bg-orange-100 text-orange-700';
  }
  return 'bg-slate-100 text-slate-700';
};

const formatDashboardDate = (date: Date) =>
  date.toLocaleDateString([], { weekday: 'long', month: 'short', day: 'numeric' });

const getProgressValue = (current: number, target: number) => {
  if (target <= 0) {
    return 0;
  }
  return Math.max(0, Math.min(100, (current / target) * 100));
};

export const Dashboard = () => {
  const [userData, setUserData] = useState<StoredUserProfile | null>(null);
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [isCameraOpen, setIsCameraOpen] = useState(false);
  const [dailyStats, setDailyStats] = useState<DailyNutritionStats | null>(null);
  const [recommendation, setRecommendation] = useState<DailyRecommendationResponse | null>(null);
  const [recentMeals, setRecentMeals] = useState<MealLogResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  useEffect(() => {
    setUserData(getStoredUserProfile());
  }, []);

  useEffect(() => {
    if (!userData) {
      return;
    }

    if (!userData.userId) {
      setDailyStats(null);
      setRecommendation(null);
      setRecentMeals([]);
      setIsLoading(false);
      return;
    }

    let isCancelled = false;

    const loadDashboardData = async () => {
      try {
        setIsLoading(true);
        const [statsResult, mealsResult, recommendationResult] = await Promise.allSettled([
          fetchDailyNutritionStats(userData.userId!, formatApiDate(selectedDate)),
          fetchMealLogs(userData.userId!),
          fetchDailyRecommendation(userData.userId!, formatApiDate(selectedDate)),
        ]);

        if (statsResult.status !== 'fulfilled') {
          throw statsResult.reason;
        }
        if (mealsResult.status !== 'fulfilled') {
          throw mealsResult.reason;
        }

        if (!isCancelled) {
          setDailyStats(statsResult.value);
          setRecentMeals(mealsResult.value);
          setRecommendation(recommendationResult.status === 'fulfilled' ? recommendationResult.value : null);
        }
      } catch (error) {
        if (!isCancelled) {
          toast({
            title: 'Unable to load dashboard data',
            description: error instanceof Error ? error.message : 'Please try again.',
            variant: 'destructive',
          });
        }
      } finally {
        if (!isCancelled) {
          setIsLoading(false);
        }
      }
    };

    void loadDashboardData();

    return () => {
      isCancelled = true;
    };
  }, [selectedDate, userData]);

  // Generate week dates around selected date
  const getWeekDates = (centerDate: Date) => {
    const dates = [];
    const startOfWeek = new Date(centerDate);
    startOfWeek.setDate(centerDate.getDate() - 3); // 3 days before center

    for (let i = 0; i < 7; i++) {
      const date = new Date(startOfWeek);
      date.setDate(startOfWeek.getDate() + i);
      dates.push(date);
    }
    return dates;
  };

  const weekDates = getWeekDates(selectedDate);
  const days = ['S', 'M', 'T', 'W', 'T', 'F', 'S'];

  const handleDateNavigation = (direction: 'prev' | 'next') => {
    const newDate = new Date(selectedDate);
    newDate.setDate(selectedDate.getDate() + (direction === 'next' ? 1 : -1));
    setSelectedDate(newDate);
  };

  const handleDateSelect = (date: Date) => {
    setSelectedDate(date);
  };

  const currentCalories = Math.round(dailyStats?.total_calories ?? 0);
  const targetCalories = Math.round(recommendation?.calorie_target ?? userData?.targetCalories ?? 2200);
  const caloriesLeft = targetCalories - currentCalories;

  const proteinConsumed = Math.round(dailyStats?.total_protein_g ?? 0);
  const targetProtein = Math.round(recommendation?.protein_target_g ?? userData?.targetProtein ?? 150);

  const carbsConsumed = Math.round(dailyStats?.total_carbs_g ?? 0);
  const targetCarbs = userData?.targetCarbs ?? 275;

  const fatsConsumed = Math.round(dailyStats?.total_fat_g ?? 0);
  const targetFats = userData?.targetFats ?? 73;

  const mealCount = recommendation?.meal_count ?? dailyStats?.meal_count ?? 0;
  const mealCountLabel = mealCount === 1 ? 'meal' : 'meals';
  const selectedDateLabel = formatDashboardDate(selectedDate);
  const isSelectedDateToday = selectedDate.toDateString() === new Date().toDateString();
  const calorieBalanceLabel = caloriesLeft > 0 ? `${caloriesLeft} left` : caloriesLeft < 0 ? `${Math.abs(caloriesLeft)} over` : 'On target';
  const leadingSuggestion = recommendation?.suggestions[0] ?? null;
  const secondarySuggestions = recommendation?.suggestions.slice(1, 3) ?? [];

  const handleCameraClick = () => {
    setIsCameraOpen(true);
  };

  const handlePhotoCapture = async (imageBlob: Blob) => {
    if (!userData?.userId) {
      toast({
        title: 'Profile not ready',
        description: 'Complete onboarding before analyzing meals.',
        variant: 'destructive',
      });
      return;
    }

    try {
      setIsAnalyzing(true);
      toast({
        title: 'Analyzing meal',
        description: 'Processing your food image for calorie analysis...',
      });

      const mimeType = imageBlob.type || 'image/jpeg';
      const extension = mimeType.includes('png') ? 'png' : 'jpg';
      const imageFile = imageBlob instanceof File ? imageBlob : new File([imageBlob], `meal-${Date.now()}.${extension}`, { type: mimeType });
      const analysisResponse = await analyzeMealImage({
        image: imageFile,
        userId: userData.userId,
        mealTime: new Date().toISOString(),
        saveResult: true,
      });

      const [statsResult, mealsResult, recommendationResult] = await Promise.allSettled([
        fetchDailyNutritionStats(userData.userId, formatApiDate(selectedDate)),
        fetchMealLogs(userData.userId),
        fetchDailyRecommendation(userData.userId, formatApiDate(selectedDate)),
      ]);

      if (statsResult.status !== 'fulfilled') {
        throw statsResult.reason;
      }
      if (mealsResult.status !== 'fulfilled') {
        throw mealsResult.reason;
      }

      setDailyStats(statsResult.value);
      setRecentMeals(mealsResult.value);
      setRecommendation(recommendationResult.status === 'fulfilled' ? recommendationResult.value : null);
      toast({
        title: 'Meal analyzed',
        description: `${analysisResponse.analysis.meal_name} · ${Math.round(analysisResponse.analysis.estimated_calories)} cal`,
      });
    } catch (error) {
      toast({
        title: 'Meal analysis failed',
        description: error instanceof Error ? error.message : 'Please try again.',
        variant: 'destructive',
      });
    } finally {
      setIsAnalyzing(false);
    }
  };

  if (!userData || isLoading) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>;
  }

  const caloriesData = [
    { name: 'consumed', value: currentCalories },
    { name: 'remaining', value: Math.max(0, targetCalories - currentCalories) }
  ];

  return (
    <div className="min-h-screen bg-background p-3 pb-20">
      {/* Top Bar */}
      <div className="flex items-center justify-between mb-6 px-1">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 bg-foreground rounded-lg flex items-center justify-center">
            <span className="text-background text-xs">🍎</span>
          </div>
          <h1 className="text-xl font-bold text-foreground">NutriLens</h1>
        </div>

        <div className="text-right">
          <div className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
            {isSelectedDateToday ? 'Today' : 'Selected day'}
          </div>
          <div className="text-sm font-semibold text-foreground">{mealCount} {mealCountLabel}</div>
        </div>
      </div>

      <div className="mb-4 px-1">
        <div className="text-2xl font-bold text-foreground">{isSelectedDateToday ? 'Today overview' : 'Daily overview'}</div>
        <div className="text-sm text-muted-foreground">{selectedDateLabel}</div>
      </div>

      {/* Interactive Week Calendar */}
      <div className="flex items-center justify-between mb-6 px-1">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => handleDateNavigation('prev')}
          className="p-1 h-8 w-8 rounded-full"
        >
          <ChevronLeft className="w-4 h-4" />
        </Button>
        
        <div className="flex gap-2">
          {weekDates.map((date, index) => {
            const isSelected = date.toDateString() === selectedDate.toDateString();
            const isToday = date.toDateString() === new Date().toDateString();
            
            return (
              <button
                key={index}
                onClick={() => handleDateSelect(date)}
                className="text-center focus:outline-none"
              >
                <div className="text-xs text-muted-foreground mb-1 font-medium">
                  {days[date.getDay()]}
                </div>
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold transition-all ${
                    isSelected
                      ? 'bg-foreground text-background'
                      : isToday
                      ? 'bg-accent text-accent-foreground'
                      : 'bg-muted text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                  }`}
                >
                  {date.getDate()}
                </div>
              </button>
            );
          })}
        </div>
        
        <Button
          variant="ghost"
          size="sm"
          onClick={() => handleDateNavigation('next')}
          className="p-1 h-8 w-8 rounded-full"
        >
          <ChevronRight className="w-4 h-4" />
        </Button>
      </div>

      {/* Daily Summary */}
      <div className="grid grid-cols-1 gap-3 mb-6">
        {/* Main Calorie Card */}
        <Card className="border-0 bg-card rounded-2xl shadow-sm">
          <CardContent className="p-5">
            <div className="flex items-start justify-between gap-4 mb-4">
              <div>
                <div className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Energy progress</div>
                <div className="text-sm text-muted-foreground">Target {targetCalories} kcal</div>
              </div>
              <div className="rounded-full bg-muted px-3 py-1 text-xs font-semibold text-foreground">
                {calorieBalanceLabel}
              </div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-foreground mb-1">{currentCalories}</div>
              <div className="text-sm text-muted-foreground">calories consumed</div>
              <div className="text-xs text-muted-foreground mb-4">
                {mealCount} {mealCountLabel} logged
              </div>
              <div className="relative w-16 h-16 mx-auto">
                <ChartContainer
                  config={{
                    consumed: { color: "hsl(var(--foreground))" },
                    remaining: { color: "hsl(var(--muted))" }
                  }}
                  className="w-full h-full"
                >
                  <PieChart width={64} height={64}>
                    <Pie
                      data={caloriesData}
                      cx="50%"
                      cy="50%"
                      innerRadius={20}
                      outerRadius={28}
                      dataKey="value"
                      strokeWidth={0}
                    >
                      <Cell fill="hsl(var(--foreground))" />
                      <Cell fill="hsl(var(--muted))" />
                    </Pie>
                  </PieChart>
                </ChartContainer>
                <div className="absolute inset-0 flex items-center justify-center">
                  <Flame className="w-4 h-4 text-foreground" />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Nutrients Grid */}
        <div className="grid grid-cols-3 gap-3">
          <Card className="border-0 bg-card rounded-2xl shadow-sm">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-xs text-muted-foreground">Protein</div>
                  <div className="text-lg font-bold text-foreground">{proteinConsumed}g</div>
                  <div className="text-[11px] text-muted-foreground">target {targetProtein}g</div>
                </div>
                <div className="relative w-8 h-8">
                  <Progress 
                    value={getProgressValue(proteinConsumed, targetProtein)} 
                    className="w-8 h-8 rounded-full [&>div]:bg-red-500"
                  />
                  <div className="absolute inset-0 flex items-center justify-center">
                    <Beef className="w-3 h-3 text-red-500" />
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-0 bg-card rounded-2xl shadow-sm">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-xs text-muted-foreground">Carbs</div>
                  <div className="text-lg font-bold text-foreground">{carbsConsumed}g</div>
                  <div className="text-[11px] text-muted-foreground">target {targetCarbs}g</div>
                </div>
                <div className="relative w-8 h-8">
                  <Progress 
                    value={getProgressValue(carbsConsumed, targetCarbs)} 
                    className="w-8 h-8 rounded-full [&>div]:bg-orange-500"
                  />
                  <div className="absolute inset-0 flex items-center justify-center">
                    <Wheat className="w-3 h-3 text-orange-500" />
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-0 bg-card rounded-2xl shadow-sm">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-xs text-muted-foreground">Fats</div>
                  <div className="text-lg font-bold text-foreground">{fatsConsumed}g</div>
                  <div className="text-[11px] text-muted-foreground">target {targetFats}g</div>
                </div>
                <div className="relative w-8 h-8">
                  <Progress 
                    value={getProgressValue(fatsConsumed, targetFats)} 
                    className="w-8 h-8 rounded-full [&>div]:bg-blue-500"
                  />
                  <div className="absolute inset-0 flex items-center justify-center">
                    <Droplet className="w-3 h-3 text-blue-500" />
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      <Card className="border-0 bg-card rounded-2xl mb-6 shadow-sm">
        <CardContent className="p-5 space-y-4">
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <div className="w-8 h-8 rounded-full bg-violet-100 text-violet-700 flex items-center justify-center">
                  <Sparkles className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-sm font-semibold text-foreground">Next best actions</div>
                  <div className="text-xs text-muted-foreground">{formatGoalLabel(recommendation?.goal ?? userData.goal)} · {selectedDateLabel}</div>
                </div>
              </div>
              <p className="text-sm text-muted-foreground leading-relaxed">
                {recommendation?.overview || 'Recommendations will appear after your profile and meal data sync.'}
              </p>
            </div>
            <div className="text-right shrink-0">
              <div className="text-xs text-muted-foreground">Meals today</div>
              <div className="text-lg font-bold text-foreground">{mealCount}</div>
            </div>
          </div>

          {leadingSuggestion && (
            <div className="rounded-2xl border border-violet-100 bg-violet-50 p-4 space-y-2">
              <div className="flex items-center justify-between gap-3">
                <div className="text-xs font-semibold uppercase tracking-wide text-violet-700">Recommended next step</div>
                <span className={`px-2 py-1 rounded-full text-[10px] font-semibold uppercase ${getPriorityClasses(leadingSuggestion.priority)}`}>
                  {leadingSuggestion.priority}
                </span>
              </div>
              <div className="font-semibold text-sm text-foreground">{leadingSuggestion.title}</div>
              <div className="text-sm text-muted-foreground leading-relaxed">{leadingSuggestion.message}</div>
              <div className="text-xs text-muted-foreground/80 leading-relaxed">Why: {leadingSuggestion.rationale}</div>
            </div>
          )}

          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-2xl bg-muted/60 p-3">
              <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
                <Flame className="w-3 h-3" />
                Calorie target
              </div>
              <div className="text-base font-semibold text-foreground">{Math.round(recommendation?.calorie_target ?? targetCalories)} kcal</div>
            </div>
            <div className="rounded-2xl bg-muted/60 p-3">
              <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
                <Target className="w-3 h-3" />
                Protein target
              </div>
              <div className="text-base font-semibold text-foreground">{Math.round(recommendation?.protein_target_g ?? targetProtein)} g</div>
            </div>
          </div>

          {recommendation && recommendation.focus.length > 0 && (
            <div className="space-y-2">
              <div className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Focus</div>
              <div className="flex flex-wrap gap-2">
                {recommendation.focus.slice(0, 4).map((item) => (
                  <span key={item} className="px-3 py-1 rounded-full bg-muted text-xs text-foreground">
                    {item}
                  </span>
                ))}
              </div>
            </div>
          )}

          {recommendation && recommendation.memory_signals.length > 0 && (
            <div className="space-y-2">
              <div className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Memory signals</div>
              <div className="space-y-2">
                {recommendation.memory_signals.slice(0, 2).map((signal) => (
                  <div key={signal} className="rounded-2xl bg-muted/60 px-3 py-2 text-sm text-muted-foreground leading-relaxed">
                    {signal}
                  </div>
                ))}
              </div>
            </div>
          )}

          {secondarySuggestions.length > 0 && (
            <div className="space-y-3">
              <div className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">More ideas</div>
              {secondarySuggestions.map((suggestion) => (
                <div key={suggestion.title} className="rounded-2xl border border-border/60 p-3 space-y-2">
                  <div className="flex items-center justify-between gap-3">
                    <div className="font-semibold text-sm text-foreground">{suggestion.title}</div>
                    <span className={`px-2 py-1 rounded-full text-[10px] font-semibold uppercase ${getPriorityClasses(suggestion.priority)}`}>
                      {suggestion.priority}
                    </span>
                  </div>
                  <div className="text-sm text-muted-foreground leading-relaxed">{suggestion.message}</div>
                  <div className="text-xs text-muted-foreground/80 leading-relaxed">Why: {suggestion.rationale}</div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Recently Logged */}
      <div className="mb-6">
        <h2 className="text-lg font-bold text-foreground mb-4 px-1">Recently logged</h2>
        <div className="space-y-3">
          {recentMeals.length === 0 ? (
            <Card className="border-0 bg-card rounded-2xl shadow-sm">
              <CardContent className="p-4">
                <div className="text-sm text-muted-foreground">No meals logged yet. Tap the plus button to scan your first meal.</div>
              </CardContent>
            </Card>
          ) : (
            recentMeals.slice(0, 3).map((meal) => (
              <Card key={meal.id} className="border-0 bg-card rounded-2xl shadow-sm">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-semibold text-foreground text-sm">{meal.meal_name}</span>
                        <div className="flex items-center gap-1 bg-green-100 text-green-700 px-2 py-0.5 rounded-full">
                          <Scan className="w-3 h-3" />
                          <span className="text-xs font-medium">Scanned</span>
                        </div>
                      </div>
                      <div className="text-xs text-muted-foreground">{formatMealTime(meal.meal_time)}</div>
                    </div>
                    <div className="text-sm font-bold text-foreground">{Math.round(meal.estimated_calories)} cal</div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      </div>

      <Card className="border-0 bg-gradient-to-r from-pink-50 to-orange-50 rounded-2xl mb-6 shadow-sm">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <div className="inline-block bg-pink-500 text-white px-3 py-1 rounded-full text-xs font-bold mb-2">
                80% off
              </div>
              <h3 className="text-sm font-bold text-foreground">Trial ends today!</h3>
            </div>
            <div className="text-center mr-3">
              <div className="text-lg font-bold text-foreground">23:56:43</div>
            </div>
            <Button className="bg-foreground text-background hover:bg-foreground/90 rounded-full px-4 py-2 text-sm">
              Upgrade
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Floating Action Button */}
      <Button
        onClick={handleCameraClick}
        disabled={isAnalyzing}
        className="fixed bottom-20 right-4 w-12 h-12 rounded-full bg-foreground hover:bg-foreground/90 text-background shadow-lg z-10"
        size="icon"
      >
        <Plus className="w-5 h-5" />
      </Button>

      {/* Camera Capture Modal */}
      <CameraCapture
        isOpen={isCameraOpen}
        onClose={() => setIsCameraOpen(false)}
        onCapture={handlePhotoCapture}
      />

      <BottomNavigation />
    </div>
  );
};